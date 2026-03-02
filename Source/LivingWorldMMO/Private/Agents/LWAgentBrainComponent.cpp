#include "Agents/LWAgentBrainComponent.h"

#include "Agents/LWAgentSubsystem.h"
#include "Events/LWEventBusSubsystem.h"
#include "GameFramework/Actor.h"
#include "GameplayTagsManager.h"
#include "WorldState/LWWorldStateSubsystem.h"

ULWAgentBrainComponent::ULWAgentBrainComponent()
{
    PrimaryComponentTick.bCanEverTick = true;
}

void ULWAgentBrainComponent::BeginPlay()
{
    Super::BeginPlay();
    AgentId = FGuid::NewGuid();

    if (ULWAgentSubsystem* AgentSubsystem = GetWorld()->GetSubsystem<ULWAgentSubsystem>())
    {
        AgentSubsystem->RegisterBrain(this);
    }
}

void ULWAgentBrainComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    UWorld* World = GetWorld();
    if (World)
    {
        if (ULWAgentSubsystem* AgentSubsystem = World->GetSubsystem<ULWAgentSubsystem>())
        {
            AgentSubsystem->UnregisterBrain(this);
        }

        if (ULWWorldStateSubsystem* WS = World->GetSubsystem<ULWWorldStateSubsystem>())
        {
            WS->RemoveAgent(AgentId);
        }
    }

    Super::EndPlay(EndPlayReason);
}

void ULWAgentBrainComponent::TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
    Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

    const float Interval = (CurrentLOD == ELWAgentLOD::Micro) ? 0.1f : (CurrentLOD == ELWAgentLOD::Meso ? 0.5f : 2.0f);
    Accumulator += DeltaTime;
    if (Accumulator < Interval)
    {
        return;
    }

    Accumulator = 0.0f;
    FLWAgentRuntimeState State = BuildRuntimeState();

    if (ULWWorldStateSubsystem* WorldState = GetWorld()->GetSubsystem<ULWWorldStateSubsystem>())
    {
        WorldState->RegisterOrUpdateAgent(State);
    }

    if (CurrentLOD == ELWAgentLOD::Micro && FMath::FRand() < 0.02f)
    {
        FLWWorldEvent Event;
        Event.EventId = FGuid::NewGuid();
        const FGameplayTag InsultTag = UGameplayTagsManager::Get().RequestGameplayTag(TEXT("Event.Social.Insult"), false);
        if (!InsultTag.IsValid())
        {
            UE_LOG(LogTemp, Warning, TEXT("LWAgentBrain: missing gameplay tag Event.Social.Insult, skipping social event."));
            return;
        }

        Event.EventType = InsultTag;
        Event.Location = State.Position;
        Event.Severity = 0.15f;
        if (ULWEventBusSubsystem* EventBus = GetWorld()->GetSubsystem<ULWEventBusSubsystem>())
        {
            EventBus->RaiseEvent(Event);
        }
    }
}

void ULWAgentBrainComponent::SetLOD(ELWAgentLOD NewLOD)
{
    CurrentLOD = NewLOD;
}

FLWAgentRuntimeState ULWAgentBrainComponent::BuildRuntimeState() const
{
    FLWAgentRuntimeState State;
    State.AgentId = AgentId;
    State.ArchetypeId = ArchetypeId;
    State.LOD = CurrentLOD;
    State.Faction = Faction;
    State.Position = GetOwner() ? GetOwner()->GetActorLocation() : FVector::ZeroVector;
    return State;
}
