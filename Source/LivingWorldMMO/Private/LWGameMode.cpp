#include "LWGameMode.h"

#include "Engine/World.h"

void ALWGameMode::BeginPlay()
{
    Super::BeginPlay();
    if (HasAuthority())
    {
        SpawnAgents();
    }
}

void ALWGameMode::SpawnAgents()
{
    UWorld* World = GetWorld();
    if (!World)
    {
        return;
    }

    const TArray<TSubclassOf<AActor>> Types = {MerchantClass, BanditClass, WildlifeClass};
    for (int32 TypeIndex = 0; TypeIndex < Types.Num(); ++TypeIndex)
    {
        if (!Types[TypeIndex])
        {
            continue;
        }

        for (int32 i = 0; i < SpawnPerType; ++i)
        {
            FVector Pos(500.0f * TypeIndex + i * 180.0f, TypeIndex * 1000.0f, 120.0f);
            World->SpawnActor<AActor>(Types[TypeIndex], Pos, FRotator::ZeroRotator);
        }
    }
}
