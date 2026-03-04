#include "Agents/LWAgentSubsystem.h"

#include "Agents/LWAgentBrainComponent.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

void ULWAgentSubsystem::Tick(float DeltaTime)
{
    RebalanceAccumulator += DeltaTime;
    if (RebalanceAccumulator < 0.5f)
    {
        return;
    }
    RebalanceAccumulator = 0.0f;

    UWorld* World = GetWorld();
    if (!World || World->GetNetMode() == NM_Client)
    if (!World)
    {
        return;
    }

    TArray<APawn*> PlayerPawns;
    for (FConstPlayerControllerIterator It = World->GetPlayerControllerIterator(); It; ++It)
    {
        APlayerController* PC = It->Get();
        if (!PC)
        {
            continue;
        }

        if (APawn* PlayerPawn = PC->GetPawn())
        {
            PlayerPawns.Add(PlayerPawn);
        }
    }
    TArray<AActor*> PlayerPawns;
    UGameplayStatics::GetAllActorsOfClass(GetWorld(), APawn::StaticClass(), PlayerPawns);

    for (ULWAgentBrainComponent* Brain : Brains)
    {
        if (!Brain || !Brain->GetOwner())
        {
            continue;
        }

        if (PlayerPawns.IsEmpty())
        {
            Brain->SetLOD(ELWAgentLOD::Macro);
            continue;
        }

        float ClosestSq = MAX_flt;
        float ClosestSq = TNumericLimits<float>::Max();
        const FVector AgentPos = Brain->GetOwner()->GetActorLocation();
        for (APawn* PlayerPawn : PlayerPawns)
        {
            if (!PlayerPawn || PlayerPawn == Brain->GetOwner())
            {
                continue;
            }

            ClosestSq = FMath::Min(ClosestSq, FVector::DistSquared(AgentPos, PlayerPawn->GetActorLocation()));
        }

        if (ClosestSq == MAX_flt)
        {
            Brain->SetLOD(ELWAgentLOD::Macro);
            continue;
        if (ClosestSq == TNumericLimits<float>::Max())
        {
            Brain->SetLOD(ELWAgentLOD::Macro);
            continue;
        float ClosestSq = TNumericLimits<float>::Max();
        const FVector AgentPos = Brain->GetOwner()->GetActorLocation();
        for (AActor* Pawn : PlayerPawns)
        {
            ClosestSq = FMath::Min(ClosestSq, FVector::DistSquared(AgentPos, Pawn->GetActorLocation()));
        }

        if (ClosestSq < FMath::Square(2500.0f))
        {
            Brain->SetLOD(ELWAgentLOD::Micro);
        }
        else if (ClosestSq < FMath::Square(12000.0f))
        {
            Brain->SetLOD(ELWAgentLOD::Meso);
        }
        else
        {
            Brain->SetLOD(ELWAgentLOD::Macro);
        }
    }
}

TStatId ULWAgentSubsystem::GetStatId() const
{
    RETURN_QUICK_DECLARE_CYCLE_STAT(ULWAgentSubsystem, STATGROUP_Tickables);
}

void ULWAgentSubsystem::RegisterBrain(ULWAgentBrainComponent* Brain)
{
    Brains.AddUnique(Brain);
}

void ULWAgentSubsystem::UnregisterBrain(ULWAgentBrainComponent* Brain)
{
    Brains.Remove(Brain);
}
