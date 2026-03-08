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
        return;
    }

<<<<<<< HEAD
=======
void ULWWorldStateSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
>>>>>>> origin/main
    LoadSnapshot();
}

void ULWWorldStateSubsystem::Deinitialize()
{
    UWorld* World = GetWorld();
    if (World && World->GetNetMode() != NM_Client)
    {
        SaveSnapshot();
    }

<<<<<<< HEAD
=======
    SaveSnapshot();
>>>>>>> origin/main
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
    EventJournal.Add(EventLine);

    if (EventJournal.Num() > 5000)
    {
        EventJournal.RemoveAt(0, 1000, EAllowShrinking::No);
    }
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
        return;
    }

    ULWWorldSaveGame* SaveGame = Cast<ULWWorldSaveGame>(UGameplayStatics::CreateSaveGameObject(ULWWorldSaveGame::StaticClass()));
    if (!SaveGame)
    {
        UE_LOG(LogLWWorldState, Error, TEXT("Failed to allocate save object for slot '%s'"), *SaveSlotName);
        return;
    }

    ++ServerFrame;
    SaveGame->Snapshot = BuildSnapshot();
    SaveGame->EventJournal = EventJournal;

    const bool bSaved = UGameplayStatics::SaveGameToSlot(SaveGame, SaveSlotName, 0);
    if (!bSaved)
    {
        UE_LOG(LogLWWorldState, Error, TEXT("SaveGameToSlot failed for slot '%s'"), *SaveSlotName);
    }
<<<<<<< HEAD
=======
    ULWWorldSaveGame* SaveGame = Cast<ULWWorldSaveGame>(UGameplayStatics::CreateSaveGameObject(ULWWorldSaveGame::StaticClass()));
    SaveGame->Snapshot = BuildSnapshot();
    SaveGame->EventJournal = EventJournal;
    UGameplayStatics::SaveGameToSlot(SaveGame, SaveSlotName, 0);
>>>>>>> origin/main
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
        return false;
    }

    ULWWorldSaveGame* SaveGame = Cast<ULWWorldSaveGame>(UGameplayStatics::LoadGameFromSlot(SaveSlotName, 0));
    if (!SaveGame)
    {
        UE_LOG(LogLWWorldState, Warning, TEXT("LoadGameFromSlot returned null for slot '%s'"), *SaveSlotName);
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

    return true;
}
