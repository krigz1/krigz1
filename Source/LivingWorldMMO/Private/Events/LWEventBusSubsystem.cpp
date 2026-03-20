#include "Events/LWEventBusSubsystem.h"

#include "WorldState/LWWorldStateSubsystem.h"

DEFINE_LOG_CATEGORY_STATIC(LogLWEventBus, Log, All);

void ULWEventBusSubsystem::RaiseEvent(const FLWWorldEvent& EventData)
{
    RecentEvents.Add(EventData);
    if (RecentEvents.Num() > MaxRecentEvents)
    {
        RecentEvents.RemoveAt(0, RecentEvents.Num() - MaxRecentEvents, EAllowShrinking::No);
    }

    UE_LOG(LogLWEventBus, Log, TEXT("LW.EventBus id=%s type=%s severity=%.2f"),
        *EventData.EventId.ToString(EGuidFormats::DigitsWithHyphensLower),
        *EventData.EventType.ToString(),
        EventData.Severity);

    if (ULWWorldStateSubsystem* WorldState = GetWorld() ? GetWorld()->GetSubsystem<ULWWorldStateSubsystem>() : nullptr)
    {
        WorldState->RecordWorldEvent(EventData);
    }

    OnEventRaised.Broadcast(EventData);
}

void ULWEventBusSubsystem::DrainRecentEvents(TArray<FLWWorldEvent>& OutEvents)
{
    OutEvents = MoveTemp(RecentEvents);
    RecentEvents.Reset();
}

void ULWEventBusSubsystem::GetRecentEvents(TArray<FLWWorldEvent>& OutEvents) const
{
    OutEvents = RecentEvents;
}
