#include "WorldState/LWWorldStateSubsystem.h"

#include "Kismet/GameplayStatics.h"
#include "WorldState/LWWorldSaveGame.h"

void ULWWorldStateSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);
    LoadSnapshot();
}

void ULWWorldStateSubsystem::Deinitialize()
{
    SaveSnapshot();
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
    ULWWorldSaveGame* SaveGame = Cast<ULWWorldSaveGame>(UGameplayStatics::CreateSaveGameObject(ULWWorldSaveGame::StaticClass()));
    SaveGame->Snapshot = BuildSnapshot();
    SaveGame->EventJournal = EventJournal;
    UGameplayStatics::SaveGameToSlot(SaveGame, SaveSlotName, 0);
}

bool ULWWorldStateSubsystem::LoadSnapshot()
{
    if (!UGameplayStatics::DoesSaveGameExist(SaveSlotName, 0))
    {
        return false;
    }

    ULWWorldSaveGame* SaveGame = Cast<ULWWorldSaveGame>(UGameplayStatics::LoadGameFromSlot(SaveSlotName, 0));
    if (!SaveGame)
    {
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
