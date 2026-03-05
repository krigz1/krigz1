using UnrealBuildTool;
using System.Collections.Generic;

public class LivingWorldMMOEditorTarget : TargetRules
{
    public LivingWorldMMOEditorTarget(TargetInfo Target) : base(Target)
    {
        Type = TargetType.Editor;
        DefaultBuildSettings = BuildSettingsVersion.V5;
        IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
        ExtraModuleNames.Add("LivingWorldMMO");
    }
}
