#include "Director/LWDirectorSubsystem.h"

#include "Events/LWEventBusSubsystem.h"
#include "WorldState/LWWorldStateSubsystem.h"

void ULWDirectorSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
    Super::Initialize(Collection);

    FLWZoneBudget StartBudget;
    StartBudget.ZoneId = TEXT("MVP_Valley");
    Budgets.Add(StartBudget.ZoneId, StartBudget);
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

void ULWDirectorSubsystem::RunEconomyPass()
{
    FLWWorldEvent Event;
    Event.EventId = FGuid::NewGuid();
    Event.EventType = FGameplayTag::RequestGameplayTag(TEXT("Event.Economy.PriceUpdate"));
    Event.Severity = 0.3f;
    Event.Scalars.Add(TEXT("FoodPriceDelta"), FMath::FRandRange(-0.03f, 0.07f));

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
    // Anti-entropie: mécanisme minimal pour éviter l'emballement de l'état.
    // En production MMO: clamps réputation/économie + régulateurs par région.
}
