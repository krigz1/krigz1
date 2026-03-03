#include "Net/LWReplicationGraph.h"

#include "GameFramework/GameStateBase.h"
#include "GameFramework/PlayerState.h"

void ULWReplicationGraph::InitGlobalGraphNodes()
{
    GridNode = CreateNewNode<UReplicationGraphNode_GridSpatialization2D>();
    GridNode->CellSize = 10000.0f;
    AddGlobalGraphNode(GridNode);

    AlwaysRelevantNode = CreateNewNode<UReplicationGraphNode_ActorList>();
    AddGlobalGraphNode(AlwaysRelevantNode);
}

void ULWReplicationGraph::InitConnectionGraphNodes(UNetReplicationGraphConnection* ConnectionManager)
{
    UReplicationGraphNode_AlwaysRelevant_ForConnection* Node = CreateNewNode<UReplicationGraphNode_AlwaysRelevant_ForConnection>();
    ConnectionManager->OnClientVisibleLevelNameAdd(FName(TEXT("Persistent_Level")), this);
    AddConnectionGraphNode(Node, ConnectionManager);
}

void ULWReplicationGraph::RouteAddNetworkActorToNodes(const FNewReplicatedActorInfo& ActorInfo, FGlobalActorReplicationInfo& GlobalInfo)
{
    AActor* Actor = ActorInfo.Actor;
    if (!Actor)
    {
        return;
    }

    if (Actor->IsA<APlayerState>() || Actor->IsA<AGameStateBase>())
    {
        AlwaysRelevantNode->NotifyAddNetworkActor(ActorInfo);
        return;
    }

    GridNode->AddActor_Static(ActorInfo, GlobalInfo);
}

void ULWReplicationGraph::RouteRemoveNetworkActorToNodes(const FNewReplicatedActorInfo& ActorInfo)
{
    if (AlwaysRelevantNode)
    {
        AlwaysRelevantNode->NotifyRemoveNetworkActor(ActorInfo);
    }

    if (GridNode)
    {
        GridNode->RemoveActor_Static(ActorInfo);
    }
}
