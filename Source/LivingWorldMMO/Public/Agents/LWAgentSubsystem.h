#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "LWAgentSubsystem.generated.h"

class ULWAgentBrainComponent;

UCLASS()
class LIVINGWORLDMMO_API ULWAgentSubsystem : public UTickableWorldSubsystem
{
    GENERATED_BODY()

public:
    virtual void Tick(float DeltaTime) override;
    virtual TStatId GetStatId() const override;

    UFUNCTION(BlueprintCallable)
    void RegisterBrain(ULWAgentBrainComponent* Brain);

    UFUNCTION(BlueprintCallable)
    void UnregisterBrain(ULWAgentBrainComponent* Brain);

private:
    UPROPERTY()
    TArray<TObjectPtr<ULWAgentBrainComponent>> Brains;

    float RebalanceAccumulator = 0.0f;
};
