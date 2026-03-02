#include "Agents/LWAgentCharacter.h"

#include "Agents/LWAgentBrainComponent.h"

ALWAgentCharacter::ALWAgentCharacter()
{
    AgentBrain = CreateDefaultSubobject<ULWAgentBrainComponent>(TEXT("AgentBrain"));
}
