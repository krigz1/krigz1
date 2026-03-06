#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "WorldState/LWTypes.h"
#include "LWWorldStateSubsystem.generated.h"

UCLASS(Config=Game, DefaultConfig)
class LIVINGWORLDMMO_API ULWWorldStateSubsystem : public UWorldSubsystem
{
    GENERATED_BODY()

public:
    virtual void Initialize(FSubsystemCollectionBase& Collection) override;
    virtual void Deinitialize() override;

    UFUNCTION(BlueprintCallable)
    void RegisterOrUpdateAgent(const FLWAgentRuntimeState& State);

    UFUNCTION(BlueprintCallable)
    bool GetAgentState(const FGuid& AgentId, FLWAgentRuntimeState& OutState) const;

    UFUNCTION(BlueprintCallable)
    void RemoveAgent(const FGuid& AgentId);

    UFUNCTION(BlueprintCallable)
    void WriteEventJournal(const FString& EventLine);

    UFUNCTION(BlueprintCallable)
    void SaveSnapshot();

    UFUNCTION(BlueprintCallable)
    bool LoadSnapshot();

    UFUNCTION(BlueprintCallable)
    FLWWorldSnapshot BuildSnapshot() const;

private:
    UPROPERTY()
    TMap<FGuid, FLWAgentRuntimeState> AgentStates;

    UPROPERTY()
    TArray<FLWEconomySignal> EconomySignals;

    UPROPERTY()
    TArray<FString> EventJournal;

    int64 ServerFrame = 0;

    UPROPERTY(EditAnywhere, Config, Category="LivingWorld|Persistence")
    FString SaveSlotName = TEXT("LivingWorld_MVP");
};
