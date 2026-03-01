#include "Events/LWEventBusSubsystem.h"

void ULWEventBusSubsystem::RaiseEvent(const FLWWorldEvent& EventData)
{
    RecentEvents.Add(EventData);
    OnEventRaised.Broadcast(EventData);
}

void ULWEventBusSubsystem::DrainRecentEvents(TArray<FLWWorldEvent>& OutEvents)
{
    OutEvents = MoveTemp(RecentEvents);
    RecentEvents.Reset();
}
