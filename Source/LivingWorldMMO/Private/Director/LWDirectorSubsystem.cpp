#include "Director/LWDirectorSubsystem.h"

#include "Events/LWEventBusSubsystem.h"
#include "Misc/ConfigCacheIni.h"
#include "WorldState/LWWorldStateSubsystem.h"

void ULWDirectorSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    FLWZoneBudget StartBudget;
    StartBudget.ZoneId = TEXT("MVP_Valley");
    Budgets.Add(StartBudget.ZoneId, StartBudget);

    GConfig->GetBool(TEXT("/Script/LivingWorldMMO.LWDirectorSubsystem"), TEXT("bCodeElisabethEnabled"), bCodeElisabethEnabled, GGameIni);
    GConfig->GetFloat(TEXT("/Script/LivingWorldMMO.LWDirectorSubsystem"), TEXT("MaxAutonomousSeverity"), MaxAutonomousSeverity, GGameIni);
}

void ULWDirectorSubsystem::Tick(float DeltaTime)
{
    EconomyAccumulator += DeltaTime;
    ConflictAccumulator += DeltaTime;

    if (EconomyAccumulator > 5.0f)
    {
        EconomyAccumulator = 0.0f;
        RunEconomyPass();
    }

    if (ConflictAccumulator > 15.0f)
    {
        ConflictAccumulator = 0.0f;
        RunConflictPass();
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

bool ULWDirectorSubsystem::ValidateAgainstCodeElisabeth(const FLWWorldEvent& CandidateEvent, FString& OutReason) const
{
    if (!bCodeElisabethEnabled)
    {
        return true;
    }

    // R3/R6/R10/R11/R400: sécurité + cohérence + stabilité avant tout.
    if (!CandidateEvent.EventType.IsValid())
    {
        OutReason = TEXT("Rejected by Code Elisabeth: missing event gameplay tag.");
        return false;
    }

    if (CandidateEvent.Severity < 0.0f || CandidateEvent.Severity > 1.0f)
    {
        OutReason = TEXT("Rejected by Code Elisabeth: severity must stay in [0..1].");
        return false;
    }

    // R426/R427/R431: action majeure => validation explicite du Créateur.
    if (RequiresCreatorValidation(CandidateEvent))
    {
        OutReason = TEXT("Blocked by Code Elisabeth: major event requires creator validation.");
        return false;
    }

    return true;
}

bool ULWDirectorSubsystem::RequiresCreatorValidation(const FLWWorldEvent& CandidateEvent) const
{
    return CandidateEvent.Severity >= MaxAutonomousSeverity;
}

void ULWDirectorSubsystem::RunEconomyPass()
{
    FLWWorldEvent Event;
    Event.EventId = FGuid::NewGuid();
    Event.EventType = FGameplayTag::RequestGameplayTag(TEXT("Event.Economy.PriceUpdate"));
    Event.Severity = 0.3f;
    Event.Scalars.Add(TEXT("FoodPriceDelta"), FMath::FRandRange(-0.03f, 0.07f));

    FString RejectReason;
    if (!ValidateAgainstCodeElisabeth(Event, RejectReason))
    {
        if (ULWWorldStateSubsystem* WorldState = GetWorld()->GetSubsystem<ULWWorldStateSubsystem>())
        {
            WorldState->WriteEventJournal(RejectReason);
        }
        return;
    }

    if (ULWEventBusSubsystem* EventBus = GetWorld()->GetSubsystem<ULWEventBusSubsystem>())
    {
        EventBus->RaiseEvent(Event);
    }
}

void ULWDirectorSubsystem::RunConflictPass()
{
    FLWWorldEvent Event;
    Event.EventId = FGuid::NewGuid();
    Event.EventType = FGameplayTag::RequestGameplayTag(TEXT("Event.Conflict.BanditRaid"));
    Event.Location = FVector(4200.0f, -1800.0f, 0.0f);
    Event.Severity = 0.8f;

    FString RejectReason;
    if (!ValidateAgainstCodeElisabeth(Event, RejectReason))
    {
        if (ULWWorldStateSubsystem* WorldState = GetWorld()->GetSubsystem<ULWWorldStateSubsystem>())
        {
            WorldState->WriteEventJournal(RejectReason);
        }
        return;
    }

    if (ULWEventBusSubsystem* EventBus = GetWorld()->GetSubsystem<ULWEventBusSubsystem>())
    {
        EventBus->RaiseEvent(Event);
    }

    if (ULWWorldStateSubsystem* WorldState = GetWorld()->GetSubsystem<ULWWorldStateSubsystem>())
    {
        WorldState->WriteEventJournal(TEXT("Bandit raid triggered near South Gate."));
    }
}

void ULWDirectorSubsystem::RunEntropyControlPass()
{
    // Anti-entropie (Code Elisabeth R8/R47/R56/R355):
    // mécanisme MVP pour contenir la dérive du monde avant déséquilibre irréversible.
    // En production MMO: clamps réputation/économie + régulateurs par région.
}
