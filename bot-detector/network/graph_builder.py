import networkx as nx
from supabase import create_client
import os
import json
from datetime import datetime, timezone

def get_supabase():
    return create_client(
        os.getenv("SUPABASE_URL"),
        os.getenv("SUPABASE_KEY")
    )

def save_edge(source: str, target: str, edge_type: str):
    """Save a connection between two accounts."""
    supabase = get_supabase()

    # Check if edge already exists
    existing = supabase.table("account_edges")\
        .select("*")\
        .eq("source_username", source)\
        .eq("target_username", target)\
        .eq("edge_type", edge_type)\
        .execute()

    if existing.data:
        # Increment occurrence count
        edge_id = existing.data[0]["id"]
        count   = existing.data[0]["occurrence_count"] + 1
        supabase.table("account_edges")\
            .update({"occurrence_count": count})\
            .eq("id", edge_id)\
            .execute()
    else:
        # Create new edge
        supabase.table("account_edges").insert({
            "source_username":  source,
            "target_username":  target,
            "edge_type":        edge_type,
            "occurrence_count": 1
        }).execute()


def build_edges_from_profile(profile: dict, category: str):
    """
    Extract edges from a profile and save them.
    Called after every analysis.
    """
    username        = profile.get("username")
    following_list  = profile.get("following_list", [])

    # Pull all known bot usernames from database
    supabase    = get_supabase()
    known_bots  = supabase.table("bot_analyses")\
        .select("username")\
        .neq("category", "human")\
        .neq("category", "utility_bot")\
        .execute()

    known_usernames = [r["username"] for r in known_bots.data]

    # Save edges where this account follows other known bots
    for followed in following_list:
        if followed in known_usernames:
            save_edge(username, followed, "follows")


def detect_clusters():
    """
    Pull all edges from database, build a graph,
    detect communities, save botnets.
    """
    supabase = get_supabase()

    # Pull all edges
    edges = supabase.table("account_edges").select("*").execute()

    if not edges.data:
        print("[*] No edges found yet.")
        return []

    # Build graph
    G = nx.Graph()
    for edge in edges.data:
        G.add_edge(
            edge["source_username"],
            edge["target_username"],
            edge_type=edge["edge_type"],
            weight=edge["occurrence_count"]
        )

    # Detect communities
    communities = list(nx.community.greedy_modularity_communities(G))
    print(f"[*] Detected {len(communities)} clusters")

    botnets = []
    for i, community in enumerate(communities):
        members = list(community)

        if len(members) < 2:
            continue  # Skip isolated nodes

        # Find hub accounts (most connected)
        subgraph    = G.subgraph(members)
        degree_map  = dict(subgraph.degree())
        hubs        = sorted(degree_map, key=degree_map.get, reverse=True)[:3]

        # Pull categories for members
        member_data = supabase.table("bot_analyses")\
            .select("username, category, signals")\
            .in_("username", members)\
            .execute()

        categories  = [r["category"] for r in member_data.data if r["category"]]
        dominant    = max(set(categories), key=categories.count) if categories else "unknown"

        all_signals = []
        for r in member_data.data:
            if r["signals"]:
                all_signals.extend(r["signals"])
        shared = list(set(all_signals))[:5]

        # Save botnet to database
        botnet_record = supabase.table("botnets").insert({
            "category":         dominant,
            "member_count":     len(members),
            "hub_accounts":     hubs,
            "shared_signals":   shared,
            "confidence":       round(len(members) / (len(members) + 2), 2)
        }).execute()

        botnets.append({
            "members":  members,
            "hubs":     hubs,
            "category": dominant,
            "size":     len(members)
        })

        print(f"[+] Cluster {i+1}: {len(members)} accounts | "
              f"dominant={dominant} | hubs={hubs}")

    return botnets