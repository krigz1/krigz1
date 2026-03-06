# Blueprints MVP à créer

## BP_AgentBase
- Parent: `ALWAgentCharacter`
- Components:
  - Capsule
  - Mesh
  - CharacterMovement
  - AgentBrain (déjà présent côté C++)

## BP_MerchantAgent
- Parent: `BP_AgentBase`
- AgentBrain.ArchetypeId = `Merchant_T1`
- AgentBrain.Faction = `MerchantGuild`

## BP_BanditAgent
- Parent: `BP_AgentBase`
- AgentBrain.ArchetypeId = `Bandit_T1`
- AgentBrain.Faction = `Bandits`

## BP_WildlifeAgent
- Parent: `BP_AgentBase`
- AgentBrain.ArchetypeId = `Wildlife_Deer`
- AgentBrain.Faction = `Wildlife`

## BP_LWGameMode
- Parent: `ALWGameMode`
- MerchantClass = `BP_MerchantAgent`
- BanditClass = `BP_BanditAgent`
- WildlifeClass = `BP_WildlifeAgent`
- SpawnPerType = `8`
