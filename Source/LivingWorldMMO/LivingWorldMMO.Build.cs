using UnrealBuildTool;

public class LivingWorldMMO : ModuleRules
{
    public LivingWorldMMO(ReadOnlyTargetRules Target) : base(Target)
    {
        PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

        PublicDependencyModuleNames.AddRange(new[]
        {
            "Core",
            "CoreUObject",
            "Engine",
            "InputCore",
            "EnhancedInput",
            "AIModule",
            "GameplayTasks",
            "GameplayTags",
            "GameplayAbilities",
            "NavigationSystem",
            "ReplicationGraph",
            "MassEntity",
            "MassCommon",
            "MassSpawner",
            "NetCore"
        });

        PrivateDependencyModuleNames.AddRange(new[]
        {
            "DeveloperSettings",
            "Json",
            "JsonUtilities"
        });
    }
}
