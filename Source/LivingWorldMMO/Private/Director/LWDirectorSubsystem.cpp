#include "Director/LWDirectorSubsystem.h"

#include "Events/LWEventBusSubsystem.h"
#include "GameplayTagsManager.h"
#include "WorldState/LWWorldStateSubsystem.h"

DEFINE_LOG_CATEGORY_STATIC(LogLWDirector, Log, All);

void ULWDirectorSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    FLWZoneBudget StartBudget;
    StartBudget.ZoneId = TEXT("MVP_Valley");
    Budgets.Add(StartBudget.ZoneId, StartBudget);

    if (bDeterministic)
    {
        RandomStream.Initialize(DeterministicSeed);
    }
    else
    {
        RandomStream.GenerateNewSeed();
    }

    const UGameplayTagsManager& TagsManager = UGameplayTagsManager::Get();
    PriceUpdateTag = TagsManager.RequestGameplayTag(TEXT("Event.Economy.PriceUpdate"), false);
    BanditRaidTag = TagsManager.RequestGameplayTag(TEXT("Event.Conflict.BanditRaid"), false);
    WildlifeDisturbanceTag = TagsManager.RequestGameplayTag(TEXT("Event.Wildlife.Disturbance"), false);
}

void ULWDirectorSubsystem::Tick(float DeltaTime)
{
    UWorld* World = GetWorld();
    if (!World || World->GetNetMode() == NM_Client)
    {
        return;
    }

    EconomyAccumulator += DeltaTime;
    ConflictAccumulator += DeltaTime;
    WildlifeAccumulator += DeltaTime;

    if (EconomyAccumulator >= EconomyIntervalSeconds)
    {
        EconomyAccumulator = 0.0f;
        RunEconomyPass();
    }

    if (ConflictAccumulator >= ConflictIntervalSeconds)
    {
        ConflictAccumulator = 0.0f;
        RunConflictPass();
    }

    if (WildlifeAccumulator >= WildlifeIntervalSeconds)
    {
        WildlifeAccumulator = 0.0f;
        RunWildlifePass();
    }

    RunEntropyControlPass();
}

TStatId ULWDirectorSubsystem::GetStatId() const
{
    RETURN_QUICK_DECLARE_CYCLE_STAT(ULWDirectorSubsystem, STATGROUP_Tickables);
}

void ULWDirectorSubsystem::SetZoneBudget(const FLWZoneBudget& Budget)
{
    Budgets.Add(Budget.ZoneId, Budget);
}

FString ULWDirectorSubsystem::GetDirectorStatus() const
{
    return LastDirectorDecision;
}

bool ULWDirectorSubsystem::ValidateAgainstCodeElisabeth(const FLWWorldEvent& CandidateEvent, FString& OutReason) const
{
    if (!bCodeElisabethEnabled)
    {
        return true;
    }

    if (!CandidateEvent.EventType.IsValid())
    {
        OutReason = TEXT("Rejected: missing event gameplay tag");
        return false;
    }

    if (CandidateEvent.Severity < 0.0f || CandidateEvent.Severity > 1.0f)
    {
        OutReason = TEXT("Rejected: severity must stay in [0..1]");
        return false;
    }

    if (RequiresCreatorValidation(CandidateEvent))
    {
        OutReason = TEXT("Rejected: major event requires creator validation");
        return false;
    }

    return true;
}

bool ULWDirectorSubsystem::RequiresCreatorValidation(const FLWWorldEvent& CandidateEvent) const
{
    return CandidateEvent.Severity >= MaxAutonomousSeverity;
}

bool ULWDirectorSubsystem::EmitDirectorEvent(FLWWorldEvent& Event, const FString& AcceptedMessage, const FString& RejectedMessagePrefix)
{
    FString RejectReason;
    if (!ValidateAgainstCodeElisabeth(Event, RejectReason))
    {
        LastDirectorDecision = RejectReason;
        UE_LOG(LogLWDirector, Warning, TEXT("LW.Director rejected type=%s reason=%s"), *Event.EventType.ToString(), *RejectReason);
        if (ULWWorldStateSubsystem* WorldState = GetWorld()->GetSubsystem<ULWWorldStateSubsystem>())
        {
            WorldState->WriteEventJournal(FString::Printf(TEXT("%s %s"), *RejectedMessagePrefix, *RejectReason));
        }
        return false;
    }

    if (ULWEventBusSubsystem* EventBus = GetWorld()->GetSubsystem<ULWEventBusSubsystem>())
    {
        EventBus->RaiseEvent(Event);
    }

    LastDirectorDecision = AcceptedMessage;
    UE_LOG(LogLWDirector, Log, TEXT("LW.Director accepted id=%s type=%s severity=%.2f"),
        *Event.EventId.ToString(EGuidFormats::DigitsWithHyphensLower),
        *Event.EventType.ToString(),
        Event.Severity);
    if (ULWWorldStateSubsystem* WorldState = GetWorld()->GetSubsystem<ULWWorldStateSubsystem>())
    {
        WorldState->WriteEventJournal(AcceptedMessage);
    }

    return true;
}

void ULWDirectorSubsystem::RunEconomyPass()
{
    if (!PriceUpdateTag.IsValid())
    {
        UE_LOG(LogLWDirector, Warning, TEXT("LW.Director missing gameplay tag Event.Economy.PriceUpdate, skipping economy pass."));
        LastDirectorDecision = TEXT("EconomySkippedMissingTag");
        return;
    }

    FLWWorldEvent Event;
    Event.EventId = FGuid::NewGuid();
    Event.EventType = PriceUpdateTag;
    Event.Severity = 0.30f;
    Event.Location = FVector::ZeroVector;
    Event.Scalars.Add(TEXT("FoodPriceDelta"), RandomStream.FRandRange(-0.10f, 0.10f));

    EmitDirectorEvent(Event,
        FString::Printf(TEXT("Director accepted economy update delta=%.2f"), Event.Scalars[TEXT("FoodPriceDelta")]),
        TEXT("Director rejected economy update:"));
}

void ULWDirectorSubsystem::RunConflictPass()
{
    if (!BanditRaidTag.IsValid())
    {
        UE_LOG(LogLWDirector, Warning, TEXT("LW.Director missing gameplay tag Event.Conflict.BanditRaid, skipping conflict pass."));
        LastDirectorDecision = TEXT("ConflictSkippedMissingTag");
        return;
    }

    FLWWorldEvent Event;
    Event.EventId = FGuid::NewGuid();
    Event.EventType = BanditRaidTag;
    Event.Location = BanditRaidLocation;
    Event.Severity = 0.80f;

    EmitDirectorEvent(Event,
        TEXT("Director accepted bandit raid near south gate"),
        TEXT("Director rejected bandit raid:"));
}

void ULWDirectorSubsystem::RunWildlifePass()
{
    if (!WildlifeDisturbanceTag.IsValid())
    {
        UE_LOG(LogLWDirector, Warning, TEXT("LW.Director missing gameplay tag Event.Wildlife.Disturbance, skipping wildlife pass."));
        LastDirectorDecision = TEXT("WildlifeSkippedMissingTag");
        return;
    }

    FLWWorldEvent Event;
    Event.EventId = FGuid::NewGuid();
    Event.EventType = WildlifeDisturbanceTag;
    Event.Location = WildlifeDisturbanceLocation;
    Event.Severity = 0.45f;
    Event.Scalars.Add(TEXT("MigrationDistance"), RandomStream.FRandRange(300.0f, 900.0f));

    EmitDirectorEvent(Event,
        TEXT("Director accepted wildlife disturbance in valley wildlands"),
        TEXT("Director rejected wildlife disturbance:"));
}

void ULWDirectorSubsystem::RunEntropyControlPass()
{
    // WorldProof_SmallScale: explicit no-op anti-entropy hook kept to preserve architecture.
}
