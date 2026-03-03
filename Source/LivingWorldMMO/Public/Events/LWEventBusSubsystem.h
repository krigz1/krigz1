#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "GameplayTagContainer.h"
#include "LWEventBusSubsystem.generated.h"

USTRUCT(BlueprintType)
struct FLWWorldEvent
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FGuid EventId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FGameplayTag EventType;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FVector Location = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float Severity = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TMap<FName, float> Scalars;
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FLWEventRaised, const FLWWorldEvent&, EventData);

UCLASS()
class LIVINGWORLDMMO_API ULWEventBusSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()

public:
    UPROPERTY(BlueprintAssignable)
    FLWEventRaised OnEventRaised;

    UFUNCTION(BlueprintCallable)
    void RaiseEvent(const FLWWorldEvent& EventData);

    UFUNCTION(BlueprintCallable)
    void DrainRecentEvents(TArray<FLWWorldEvent>& OutEvents);

private:
    UPROPERTY()
    TArray<FLWWorldEvent> RecentEvents;
};
