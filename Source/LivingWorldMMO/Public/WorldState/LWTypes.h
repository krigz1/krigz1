#pragma once

#include "CoreMinimal.h"
#include "GameplayTagContainer.h"
#include "LWTypes.generated.h"

UENUM(BlueprintType)
enum class ELWAgentLOD : uint8
{
    Micro UMETA(DisplayName="Micro"),
    Meso UMETA(DisplayName="Meso"),
    Macro UMETA(DisplayName="Macro")
};

UENUM(BlueprintType)
enum class ELWFaction : uint8
{
    Neutral,
    CityGuard,
    MerchantGuild,
    Bandits,
    Wildlife
};

USTRUCT(BlueprintType)
struct FLWNeedState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float Hunger = 0.2f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float Safety = 0.8f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float Wealth = 0.5f;
};

USTRUCT(BlueprintType)
struct FLWAgentRuntimeState
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FGuid AgentId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FName ArchetypeId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    ELWAgentLOD LOD = ELWAgentLOD::Macro;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    ELWFaction Faction = ELWFaction::Neutral;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FVector Position = FVector::ZeroVector;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FLWNeedState Needs;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FGameplayTagContainer ContextTags;
};

USTRUCT(BlueprintType)
struct FLWZoneBudget
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FName ZoneId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    int32 MicroAgentBudget = 30;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    int32 MesoAgentBudget = 300;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    int32 MacroAgentBudget = 3000;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float MaxServerMsPerTick = 4.0f;
};

USTRUCT(BlueprintType)
struct FLWEconomySignal
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FName SettlementId;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    FGameplayTag ItemTag;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float Demand = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float Supply = 1.0f;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    float PriceIndex = 1.0f;
};

USTRUCT(BlueprintType)
struct FLWWorldSnapshot
{
    GENERATED_BODY()

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    int64 ServerFrame = 0;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TArray<FLWAgentRuntimeState> Agents;

    UPROPERTY(EditAnywhere, BlueprintReadWrite)
    TArray<FLWEconomySignal> EconomySignals;
};
