#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "WorldState/LWTypes.h"
#include "LWWorldSaveGame.generated.h"

UCLASS()
class LIVINGWORLDMMO_API ULWWorldSaveGame : public USaveGame
{
    GENERATED_BODY()

public:
    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FLWWorldSnapshot Snapshot;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TArray<FString> EventJournal;
};
