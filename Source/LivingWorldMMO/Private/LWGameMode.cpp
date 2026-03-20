#include "LWGameMode.h"

#include "Agents/LWAgentBrainComponent.h"
#include "Engine/Engine.h"
#include "Engine/World.h"
#include "Events/LWEventBusSubsystem.h"
#include "GameFramework/Actor.h"
#include "WorldState/LWWorldStateSubsystem.h"
#include "Director/LWDirectorSubsystem.h"

DEFINE_LOG_CATEGORY_STATIC(LogLWGameMode, Log, All);

ALWGameMode::ALWGameMode()
{
    PrimaryActorTick.bCanEverTick = true;
}

void ALWGameMode::BeginPlay()
{
    Super::BeginPlay();

    if (!HasAuthority())
    {
        return;
    }

    if (ULWEventBusSubsystem* EventBus = GetWorld()->GetSubsystem<ULWEventBusSubsystem>())
    {
        EventBus->OnEventRaised.AddDynamic(this, &ALWGameMode::HandleWorldEvent);
    }

    SpawnAgents();
    RefreshOverlay();
}

void ALWGameMode::Tick(float DeltaSeconds)
{
    Super::Tick(DeltaSeconds);

    if (!HasAuthority())
    {
        return;
    }

    OverlayAccumulator += DeltaSeconds;
    if (OverlayAccumulator >= OverlayRefreshSeconds)
    {
        OverlayAccumulator = 0.0f;
        RefreshOverlay();
    }

    AutoSaveAccumulator += DeltaSeconds;
    if (AutoSaveAccumulator >= AutoSaveIntervalSeconds)
    {
        AutoSaveAccumulator = 0.0f;
        if (ULWWorldStateSubsystem* WorldState = GetWorld()->GetSubsystem<ULWWorldStateSubsystem>())
        {
            WorldState->SaveSnapshot();
        }
    }
}

void ALWGameMode::HandleWorldEvent(const FLWWorldEvent& EventData)
{
    LastObservedEvent = EventData;
    bHasObservedEvent = true;

    UE_LOG(LogLWGameMode, Log, TEXT("LW.WorldProof event=%s id=%s severity=%.2f location=%s"),
        *EventData.EventType.ToString(),
        *EventData.EventId.ToString(EGuidFormats::DigitsWithHyphensLower),
        EventData.Severity,
        *EventData.Location.ToCompactString());

    RefreshOverlay();

    if (ULWWorldStateSubsystem* WorldState = GetWorld()->GetSubsystem<ULWWorldStateSubsystem>())
    {
        WorldState->SaveSnapshot();
    }
}

void ALWGameMode::SpawnAgents()
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    const int32 TotalAgents = MerchantCount + BanditCount + WildlifeCount;
    UE_LOG(LogLWGameMode, Log, TEXT("LW.WorldProof spawning %d agents (merchant=%d bandit=%d wildlife=%d)"), TotalAgents, MerchantCount, BanditCount, WildlifeCount);

    SpawnAgentFamily(MerchantClass, MerchantCount, ELWFaction::MerchantGuild, FVector(0.0f, -1200.0f, 140.0f), FVector(180.0f, 120.0f, 0.0f));
    SpawnAgentFamily(BanditClass, BanditCount, ELWFaction::Bandits, FVector(1200.0f, 800.0f, 140.0f), FVector(160.0f, 120.0f, 0.0f));
    SpawnAgentFamily(WildlifeClass, WildlifeCount, ELWFaction::Wildlife, FVector(-1400.0f, 1800.0f, 140.0f), FVector(220.0f, 140.0f, 0.0f));
}

void ALWGameMode::SpawnAgentFamily(const TSubclassOf<AActor>& AgentClass, int32 Count, ELWFaction FamilyFaction, const FVector& Origin, const FVector& Step)
{
    UWorld* World = GetWorld();
    if (!World || !AgentClass || Count <= 0)
    {
        return;
    }

    for (int32 Index = 0; Index < Count; ++Index)
    {
        const int32 Row = Index / 4;
        const int32 Col = Index % 4;
        const FVector SpawnLocation = Origin + FVector(Row * Step.X, Col * Step.Y, 0.0f);
        AActor* SpawnedActor = World->SpawnActor<AActor>(AgentClass, SpawnLocation, FRotator::ZeroRotator);
        if (!SpawnedActor)
        {
            continue;
        }

        if (ULWAgentBrainComponent* Brain = SpawnedActor->FindComponentByClass<ULWAgentBrainComponent>())
        {
            Brain->Faction = FamilyFaction;
            switch (FamilyFaction)
            {
            case ELWFaction::MerchantGuild:
                Brain->ArchetypeId = TEXT("Merchant_T1");
                break;
            case ELWFaction::Bandits:
                Brain->ArchetypeId = TEXT("Bandit_T1");
                break;
            case ELWFaction::Wildlife:
                Brain->ArchetypeId = TEXT("Wildlife_T1");
                break;
            default:
                Brain->ArchetypeId = TEXT("Neutral_T1");
                break;
            }
        }
    }
}

void ALWGameMode::RefreshOverlay()
{
    if (!bEnableWorldProofOverlay || !GEngine)
    {
        return;
    }

    GEngine->AddOnScreenDebugMessage(991001, OverlayRefreshSeconds + 0.1f, FColor::Green, BuildOverlayText());
}

FString ALWGameMode::BuildOverlayText() const
{
    const UWorld* World = GetWorld();
    const ULWWorldStateSubsystem* WorldState = World ? World->GetSubsystem<ULWWorldStateSubsystem>() : nullptr;
    const ULWEventBusSubsystem* EventBus = World ? World->GetSubsystem<ULWEventBusSubsystem>() : nullptr;
    const ULWDirectorSubsystem* Director = World ? World->GetSubsystem<ULWDirectorSubsystem>() : nullptr;

    const int32 AgentCount = WorldState ? WorldState->GetTrackedAgentCount() : 0;
    const int32 EventCount = EventBus ? EventBus->GetRecentEventCount() : 0;
    const FString LastEventText = bHasObservedEvent ? LastObservedEvent.EventType.ToString() : TEXT("None");
    const FString SaveStatus = WorldState ? WorldState->GetLastPersistenceStatus() : TEXT("NoState");
    const FString DirectorStatus = Director ? Director->GetDirectorStatus() : TEXT("NoDirector");

    return FString::Printf(
        TEXT("WorldProof_SmallScale\nAgents=%d\nRecentEvents=%d\nLastEvent=%s\nDirector=%s\nPersistence=%s"),
        AgentCount,
        EventCount,
        *LastEventText,
        *DirectorStatus,
        *SaveStatus);
}
