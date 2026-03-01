#include "Agents/LWAgentSubsystem.h"

#include "Agents/LWAgentBrainComponent.h"
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

    TArray<AActor*> PlayerPawns;
    UGameplayStatics::GetAllActorsOfClass(GetWorld(), APawn::StaticClass(), PlayerPawns);

    for (ULWAgentBrainComponent* Brain : Brains)
    {
        if (!Brain || !Brain->GetOwner())
        {
            continue;
        }

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
