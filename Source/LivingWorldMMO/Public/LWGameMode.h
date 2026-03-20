#pragma once

#include "CoreMinimal.h"
#include "Events/LWEventBusSubsystem.h"
#include "GameFramework/GameModeBase.h"
#include "LWGameMode.generated.h"

UCLASS(Config=Game)
class LIVINGWORLDMMO_API ALWGameMode : public AGameModeBase
{
    GENERATED_BODY()

public:
    ALWGameMode();

    virtual void BeginPlay() override;
    virtual void Tick(float DeltaSeconds) override;

protected:
    UPROPERTY(EditDefaultsOnly, Category="WorldProof")
    TSubclassOf<AActor> MerchantClass;

    UPROPERTY(EditDefaultsOnly, Category="WorldProof")
    TSubclassOf<AActor> BanditClass;

    UPROPERTY(EditDefaultsOnly, Category="WorldProof")
    TSubclassOf<AActor> WildlifeClass;

    UPROPERTY(EditDefaultsOnly, Config, Category="WorldProof", meta=(ClampMin="1", ClampMax="20"))
    int32 MerchantCount = 10;

    UPROPERTY(EditDefaultsOnly, Config, Category="WorldProof", meta=(ClampMin="1", ClampMax="20"))
    int32 BanditCount = 10;

    UPROPERTY(EditDefaultsOnly, Config, Category="WorldProof", meta=(ClampMin="1", ClampMax="20"))
    int32 WildlifeCount = 12;

    UPROPERTY(EditDefaultsOnly, Config, Category="WorldProof")
    float OverlayRefreshSeconds = 2.0f;

    UPROPERTY(EditDefaultsOnly, Config, Category="WorldProof")
    float AutoSaveIntervalSeconds = 10.0f;

    UPROPERTY(EditDefaultsOnly, Config, Category="WorldProof")
    bool bEnableWorldProofOverlay = true;

private:
    UFUNCTION()
    void HandleWorldEvent(const FLWWorldEvent& EventData);

    void SpawnAgents();
    void SpawnAgentFamily(const TSubclassOf<AActor>& AgentClass, int32 Count, ELWFaction FamilyFaction, const FVector& Origin, const FVector& Step);
    void RefreshOverlay();
    FString BuildOverlayText() const;

    float OverlayAccumulator = 0.0f;
    float AutoSaveAccumulator = 0.0f;

    UPROPERTY()
    FLWWorldEvent LastObservedEvent;

    UPROPERTY()
    bool bHasObservedEvent = false;
};
