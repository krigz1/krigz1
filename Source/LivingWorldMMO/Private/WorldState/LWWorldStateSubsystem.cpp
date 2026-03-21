#include "WorldState/LWWorldStateSubsystem.h"

#include "Kismet/GameplayStatics.h"
#include "WorldState/LWWorldSaveGame.h"

DEFINE_LOG_CATEGORY_STATIC(LogLWWorldState, Log, All);

void ULWWorldStateSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    UWorld* World = GetWorld();
    if (!World || World->GetNetMode() == NM_Client)
    {
        LastPersistenceStatus = TEXT("ClientNoLoad");
        return;
    }

    LastPersistenceStatus = LoadSnapshot() ? TEXT("LoadedSnapshot") : TEXT("NoSnapshotFound");
}

void ULWWorldStateSubsystem::Deinitialize()
{
    UWorld* World = GetWorld();
    if (World && World->GetNetMode() != NM_Client)
    {
        SaveSnapshot();
    }

    Super::Deinitialize();
}

void ULWWorldStateSubsystem::RegisterOrUpdateAgent(const FLWAgentRuntimeState& State)
{
    AgentStates.Add(State.AgentId, State);
}

bool ULWWorldStateSubsystem::GetAgentState(const FGuid& AgentId, FLWAgentRuntimeState& OutState) const
{
    if (const FLWAgentRuntimeState* Found = AgentStates.Find(AgentId))
    {
        OutState = *Found;
        return true;
    }

    return false;
}

void ULWWorldStateSubsystem::RemoveAgent(const FGuid& AgentId)
{
    AgentStates.Remove(AgentId);
}

void ULWWorldStateSubsystem::WriteEventJournal(const FString& EventLine)
{
    const FString Timestamp = FDateTime::UtcNow().ToString(TEXT("%Y-%m-%dT%H:%M:%SZ"));
    EventJournal.Add(FString::Printf(TEXT("[%s] %s"), *Timestamp, *EventLine));

    if (EventJournal.Num() > 5000)
    {
        EventJournal.RemoveAt(0, 1000, EAllowShrinking::No);
    }
}

void ULWWorldStateSubsystem::RecordWorldEvent(const FLWWorldEvent& EventData)
{
    WriteEventJournal(FString::Printf(TEXT("Event accepted id=%s type=%s severity=%.2f location=%s"),
        *EventData.EventId.ToString(EGuidFormats::DigitsWithHyphensLower),
        *EventData.EventType.ToString(),
        EventData.Severity,
        *EventData.Location.ToCompactString()));
}

FLWWorldSnapshot ULWWorldStateSubsystem::BuildSnapshot() const
{
    FLWWorldSnapshot Snapshot;
    Snapshot.ServerFrame = ServerFrame;
    AgentStates.GenerateValueArray(Snapshot.Agents);
    Snapshot.EconomySignals = EconomySignals;
    return Snapshot;
}

void ULWWorldStateSubsystem::SaveSnapshot()
{
    UWorld* World = GetWorld();
    if (!World || World->GetNetMode() == NM_Client)
    {
        LastPersistenceStatus = TEXT("ClientSkipSave");
        return;
    }

    ULWWorldSaveGame* SaveGame = Cast<ULWWorldSaveGame>(UGameplayStatics::CreateSaveGameObject(ULWWorldSaveGame::StaticClass()));
    if (!SaveGame)
    {
        LastPersistenceStatus = TEXT("SaveObjectAllocFailed");
        UE_LOG(LogLWWorldState, Error, TEXT("Failed to allocate save object for slot '%s'"), *SaveSlotName);
        return;
    }

    ++ServerFrame;
    SaveGame->Snapshot = BuildSnapshot();
    SaveGame->EventJournal = EventJournal;

    const bool bSaved = UGameplayStatics::SaveGameToSlot(SaveGame, SaveSlotName, 0);
    LastPersistenceStatus = bSaved ? TEXT("SavedOK") : TEXT("SaveFailed");
    if (!bSaved)
    {
        UE_LOG(LogLWWorldState, Error, TEXT("SaveGameToSlot failed for slot '%s'"), *SaveSlotName);
        return;
    }

    UE_LOG(LogLWWorldState, Log, TEXT("LW.Persistence save slot=%s agents=%d journal=%d frame=%lld"),
        *SaveSlotName,
        AgentStates.Num(),
        EventJournal.Num(),
        ServerFrame);
}

bool ULWWorldStateSubsystem::LoadSnapshot()
{
    UWorld* World = GetWorld();
    if (!World || World->GetNetMode() == NM_Client)
    {
        return false;
    }

    if (!UGameplayStatics::DoesSaveGameExist(SaveSlotName, 0))
    {
        UE_LOG(LogLWWorldState, Log, TEXT("No save snapshot present for slot '%s'"), *SaveSlotName);
        return false;
    }

    ULWWorldSaveGame* SaveGame = Cast<ULWWorldSaveGame>(UGameplayStatics::LoadGameFromSlot(SaveSlotName, 0));
    if (!SaveGame)
    {
        UE_LOG(LogLWWorldState, Warning, TEXT("LoadGameFromSlot returned null for slot '%s'"), *SaveSlotName);
        LastPersistenceStatus = TEXT("LoadFailed");
        return false;
    }

    AgentStates.Reset();
    for (const FLWAgentRuntimeState& Agent : SaveGame->Snapshot.Agents)
    {
        AgentStates.Add(Agent.AgentId, Agent);
    }

    EconomySignals = SaveGame->Snapshot.EconomySignals;
    EventJournal = SaveGame->EventJournal;
    ServerFrame = SaveGame->Snapshot.ServerFrame;
    LastPersistenceStatus = TEXT("LoadedOK");

    UE_LOG(LogLWWorldState, Log, TEXT("LW.Persistence load slot=%s agents=%d journal=%d frame=%lld"),
        *SaveSlotName,
        AgentStates.Num(),
        EventJournal.Num(),
        ServerFrame);

    return true;
}
