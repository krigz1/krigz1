#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "LWGameMode.generated.h"

UCLASS()
class LIVINGWORLDMMO_API ALWGameMode : public AGameModeBase
{
    GENERATED_BODY()

public:
    virtual void BeginPlay() override;

protected:
    UPROPERTY(EditDefaultsOnly, Category="LivingWorld")
    TSubclassOf<AActor> MerchantClass;

    UPROPERTY(EditDefaultsOnly, Category="LivingWorld")
    TSubclassOf<AActor> BanditClass;

    UPROPERTY(EditDefaultsOnly, Category="LivingWorld")
    TSubclassOf<AActor> WildlifeClass;

    UPROPERTY(EditDefaultsOnly, Category="LivingWorld")
    int32 SpawnPerType = 8;

private:
    void SpawnAgents();
};
