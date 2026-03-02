#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "WorldState/LWTypes.h"
#include "LWDirectorSubsystem.generated.h"

UCLASS()
class LIVINGWORLDMMO_API ULWDirectorSubsystem : public UTickableWorldSubsystem
{
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Tick(float DeltaTime) override;
    virtual TStatId GetStatId() const override;

    UFUNCTION(BlueprintCallable)
    void SetZoneBudget(const FLWZoneBudget& Budget);

private:
    bool ValidateAgainstCodeElisabeth(const FLWWorldEvent& CandidateEvent, FString& OutReason) const;
    bool RequiresCreatorValidation(const FLWWorldEvent& CandidateEvent) const;

    void RunEconomyPass();
    void RunConflictPass();
    void RunEntropyControlPass();

    UPROPERTY()
    TMap<FName, FLWZoneBudget> Budgets;

    bool bCodeElisabethEnabled = true;
    float MaxAutonomousSeverity = 0.85f;

    float EconomyAccumulator = 0.0f;
    float ConflictAccumulator = 0.0f;
};
