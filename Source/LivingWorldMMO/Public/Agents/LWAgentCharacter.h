#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "LWAgentCharacter.generated.h"

class ULWAgentBrainComponent;

UCLASS()
class LIVINGWORLDMMO_API ALWAgentCharacter : public ACharacter
{
    GENERATED_BODY()

public:
    ALWAgentCharacter();

protected:
    UPROPERTY(VisibleAnywhere, BlueprintReadOnly)
    TObjectPtr<ULWAgentBrainComponent> AgentBrain;
};
