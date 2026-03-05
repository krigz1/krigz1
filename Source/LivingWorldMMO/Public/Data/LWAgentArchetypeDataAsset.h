#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "WorldState/LWTypes.h"
#include "LWAgentArchetypeDataAsset.generated.h"

UCLASS(BlueprintType)
class LIVINGWORLDMMO_API ULWAgentArchetypeDataAsset : public UPrimaryDataAsset
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FName ArchetypeId;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    ELWFaction Faction;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float MoveSpeed = 400.0f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    float Aggression = 0.2f;

    UPROPERTY(EditAnywhere, BlueprintReadOnly)
    FGameplayTagContainer SpawnContextTags;
};
