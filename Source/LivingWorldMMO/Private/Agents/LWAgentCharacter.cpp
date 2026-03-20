#include "Agents/LWAgentCharacter.h"

#include "Agents/LWAgentBrainComponent.h"

ALWAgentCharacter::ALWAgentCharacter()
{
    bReplicates = true;
    SetReplicateMovement(true);
    AgentBrain = CreateDefaultSubobject<ULWAgentBrainComponent>(TEXT("AgentBrain"));
}
