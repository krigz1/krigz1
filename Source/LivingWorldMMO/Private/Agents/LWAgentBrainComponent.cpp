#include "Agents/LWAgentBrainComponent.h"

#include "Agents/LWAgentSubsystem.h"
#include "Events/LWEventBusSubsystem.h"
#include "GameFramework/Actor.h"
#include "GameplayTagsManager.h"
#include "WorldState/LWWorldStateSubsystem.h"

DEFINE_LOG_CATEGORY_STATIC(LogLWAgent, Log, All);

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

    if (ULWEventBusSubsystem* EventBus = GetWorld()->GetSubsystem<ULWEventBusSubsystem>())
    {
        EventBus->OnEventRaised.AddDynamic(this, &ULWAgentBrainComponent::HandleWorldEvent);
    }
}

void ULWAgentBrainComponent::EndPlay(const EEndPlayReason::Type EndPlayReason)
{
    UWorld* World = GetWorld();
    if (World)
    {
        if (ULWEventBusSubsystem* EventBus = World->GetSubsystem<ULWEventBusSubsystem>())
        {
            EventBus->OnEventRaised.RemoveDynamic(this, &ULWAgentBrainComponent::HandleWorldEvent);
        }

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

    if (CurrentLOD == ELWAgentLOD::Micro && FMath::FRand() < 0.005f)
    {
        FLWWorldEvent Event;
        Event.EventId = FGuid::NewGuid();
        const FGameplayTag InsultTag = UGameplayTagsManager::Get().RequestGameplayTag(TEXT("Event.Social.Insult"), false);
        if (!InsultTag.IsValid())
        {
            UE_LOG(LogLWAgent, Warning, TEXT("LW.Agent missing gameplay tag Event.Social.Insult, skipping social event."));
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
    State.ContextTags.Reset();

    if (Faction == ELWFaction::MerchantGuild)
    {
        State.ContextTags.AddTag(FGameplayTag::RequestGameplayTag(TEXT("Faction.MerchantGuild"), false));
    }
    else if (Faction == ELWFaction::Bandits)
    {
        State.ContextTags.AddTag(FGameplayTag::RequestGameplayTag(TEXT("Faction.Bandits"), false));
    }
    else if (Faction == ELWFaction::Wildlife)
    {
        State.ContextTags.AddTag(FGameplayTag::RequestGameplayTag(TEXT("Faction.Wildlife"), false));
    }

    State.Needs.Wealth = Faction == ELWFaction::MerchantGuild ? 0.9f : 0.3f;
    State.Needs.Safety = (DebugState == TEXT("Fleeing")) ? 0.2f : 0.8f;
    State.Needs.Hunger = (Faction == ELWFaction::Wildlife) ? 0.6f : 0.3f;
    return State;
}

void ULWAgentBrainComponent::HandleWorldEvent(const FLWWorldEvent& EventData)
{
    if (EventData.EventId == LastHandledEventId)
    {
        return;
    }

    LastHandledEventId = EventData.EventId;
    const FString EventTypeString = EventData.EventType.ToString();

    if (EventTypeString == TEXT("Event.Conflict.BanditRaid"))
    {
        ApplyBanditRaidReaction(EventData);
    }
    else if (EventTypeString == TEXT("Event.Economy.PriceUpdate"))
    {
        ApplyEconomyReaction(EventData);
    }
    else if (EventTypeString == TEXT("Event.Wildlife.Disturbance"))
    {
        ApplyWildlifeReaction(EventData);
    }
    else if (EventTypeString == TEXT("Event.Social.Insult"))
    {
        DebugState = TEXT("Agitated");
        UE_LOG(LogLWAgent, Log, TEXT("LW.Agent social reaction id=%s archetype=%s state=%s"),
            *AgentId.ToString(EGuidFormats::DigitsWithHyphensLower),
            *ArchetypeId.ToString(),
            *DebugState.ToString());
    }
}

void ULWAgentBrainComponent::ApplyBanditRaidReaction(const FLWWorldEvent& EventData)
{
    if (!GetOwner())
    {
        return;
    }

    if (Faction == ELWFaction::Bandits)
    {
        DebugState = TEXT("Raiding");
        GetOwner()->SetActorLocation(EventData.Location + FVector(FMath::FRandRange(-200.0f, 200.0f), FMath::FRandRange(-200.0f, 200.0f), 0.0f));
    }
    else if (Faction == ELWFaction::MerchantGuild)
    {
        DebugState = TEXT("Fleeing");
        MoveAwayFrom(EventData.Location, 650.0f);
    }
    else if (Faction == ELWFaction::Wildlife)
    {
        DebugState = TEXT("Scattered");
        MoveAwayFrom(EventData.Location, 800.0f);
    }

    UE_LOG(LogLWAgent, Log, TEXT("LW.Agent conflict reaction id=%s faction=%d state=%s"),
        *AgentId.ToString(EGuidFormats::DigitsWithHyphensLower),
        static_cast<int32>(Faction),
        *DebugState.ToString());
}

void ULWAgentBrainComponent::ApplyEconomyReaction(const FLWWorldEvent& EventData)
{
    if (Faction != ELWFaction::MerchantGuild)
    {
        return;
    }

    const float* PriceDelta = EventData.Scalars.Find(TEXT("FoodPriceDelta"));
    DebugState = (PriceDelta && *PriceDelta >= 0.0f) ? TEXT("RaisingPrices") : TEXT("Discounting");
    UE_LOG(LogLWAgent, Log, TEXT("LW.Agent economy reaction id=%s delta=%.2f state=%s"),
        *AgentId.ToString(EGuidFormats::DigitsWithHyphensLower),
        PriceDelta ? *PriceDelta : 0.0f,
        *DebugState.ToString());
}

void ULWAgentBrainComponent::ApplyWildlifeReaction(const FLWWorldEvent& EventData)
{
    if (Faction != ELWFaction::Wildlife)
    {
        return;
    }

    DebugState = TEXT("Migrating");
    MoveAwayFrom(EventData.Location, 900.0f);
    UE_LOG(LogLWAgent, Log, TEXT("LW.Agent wildlife reaction id=%s state=%s"),
        *AgentId.ToString(EGuidFormats::DigitsWithHyphensLower),
        *DebugState.ToString());
}

void ULWAgentBrainComponent::MoveAwayFrom(const FVector& SourceLocation, float Distance)
{
    if (!GetOwner())
    {
        return;
    }

    FVector Direction = GetOwner()->GetActorLocation() - SourceLocation;
    if (Direction.IsNearlyZero())
    {
        Direction = FVector::ForwardVector;
    }

    Direction = Direction.GetSafeNormal();
    const FVector TargetLocation = GetOwner()->GetActorLocation() + Direction * Distance;
    GetOwner()->SetActorLocation(TargetLocation);
}
