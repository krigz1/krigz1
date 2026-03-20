#pragma once

#include "CoreMinimal.h"
#include "Math/RandomStream.h"
#include "Subsystems/WorldSubsystem.h"
#include "WorldState/LWTypes.h"

struct FLWWorldEvent;

#include "LWDirectorSubsystem.generated.h"

UCLASS(Config=Game, DefaultConfig)
class LIVINGWORLDMMO_API ULWDirectorSubsystem : public UTickableWorldSubsystem
{
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Tick(float DeltaTime) override;
    virtual TStatId GetStatId() const override;

    UFUNCTION(BlueprintCallable)
    void SetZoneBudget(const FLWZoneBudget& Budget);

    UFUNCTION(BlueprintPure)
    FString GetDirectorStatus() const;

private:
    bool ValidateAgainstCodeElisabeth(const FLWWorldEvent& CandidateEvent, FString& OutReason) const;
    bool RequiresCreatorValidation(const FLWWorldEvent& CandidateEvent) const;

    void RunEconomyPass();
    void RunConflictPass();
    void RunWildlifePass();
    void RunEntropyControlPass();
    bool EmitDirectorEvent(FLWWorldEvent& Event, const FString& AcceptedMessage, const FString& RejectedMessagePrefix);

    UPROPERTY(EditAnywhere, Config, Category="LivingWorld|Director", meta=(ClampMin="0.1"))
    float EconomyIntervalSeconds = 5.0f;

    UPROPERTY(EditAnywhere, Config, Category="LivingWorld|Director", meta=(ClampMin="0.1"))
    float ConflictIntervalSeconds = 15.0f;

    UPROPERTY(EditAnywhere, Config, Category="LivingWorld|Director", meta=(ClampMin="0.1"))
    float WildlifeIntervalSeconds = 9.0f;

    UPROPERTY(EditAnywhere, Config, Category="LivingWorld|Director")
    FVector BanditRaidLocation = FVector(4200.0f, -1800.0f, 0.0f);

    UPROPERTY(EditAnywhere, Config, Category="LivingWorld|Director")
    FVector WildlifeDisturbanceLocation = FVector(-2400.0f, 2600.0f, 0.0f);

    UPROPERTY(EditAnywhere, Config, Category="LivingWorld|Determinism")
    bool bDeterministic = false;

    UPROPERTY(EditAnywhere, Config, Category="LivingWorld|Determinism", meta=(EditCondition="bDeterministic"))
    int32 DeterministicSeed = 1337;

    UPROPERTY(EditAnywhere, Config, Category="LivingWorld|Governance")
    bool bCodeElisabethEnabled = true;

    UPROPERTY(EditAnywhere, Config, Category="LivingWorld|Governance", meta=(ClampMin="0.0", ClampMax="1.0"))
    float MaxAutonomousSeverity = 0.85f;

    UPROPERTY()
    TMap<FName, FLWZoneBudget> Budgets;

    FRandomStream RandomStream;
    FGameplayTag PriceUpdateTag;
    FGameplayTag BanditRaidTag;
    FGameplayTag WildlifeDisturbanceTag;

    float EconomyAccumulator = 0.0f;
    float ConflictAccumulator = 0.0f;
    float WildlifeAccumulator = 0.0f;

    UPROPERTY()
    FString LastDirectorDecision = TEXT("NoDecisionYet");
};
