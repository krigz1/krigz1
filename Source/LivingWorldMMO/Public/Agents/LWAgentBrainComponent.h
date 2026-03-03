#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "WorldState/LWTypes.h"
#include "LWAgentBrainComponent.generated.h"

UCLASS(ClassGroup=(LivingWorld), meta=(BlueprintSpawnableComponent))
class LIVINGWORLDMMO_API ULWAgentBrainComponent : public UActorComponent
{
    GENERATED_BODY()

public:
    ULWAgentBrainComponent();

    virtual void BeginPlay() override;
    virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;
    virtual void TickComponent(float DeltaTime, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="LivingWorld")
    FName ArchetypeId = NAME_None;

    UPROPERTY(EditAnywhere, BlueprintReadWrite, Category="LivingWorld")
    ELWFaction Faction = ELWFaction::Neutral;

    UFUNCTION(BlueprintCallable)
    void SetLOD(ELWAgentLOD NewLOD);

    UFUNCTION(BlueprintCallable)
    ELWAgentLOD GetCurrentLOD() const { return CurrentLOD; }

    UFUNCTION(BlueprintCallable)
    FLWAgentRuntimeState BuildRuntimeState() const;

private:
    UPROPERTY()
    FGuid AgentId;

    UPROPERTY()
    ELWAgentLOD CurrentLOD = ELWAgentLOD::Macro;

    float Accumulator = 0.0f;
};
