"use client";

import { useEffect, useRef } from "react";
import { Network } from "vis-network";
import { DataSet } from "vis-data";

const filename = "current_2025-08-10_08-52-48";

interface GraphNode {
  id: string;
  name: string;
  type: string;
}

interface GraphEdge {
  source: string;
  target: string;
  type: string;
}

interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export default function Graph() {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);

  useEffect(() => {
    const loadGraphData = async () => {
      try {
        const response = await fetch(`/models/${filename}.json`);
        const data: GraphData = await response.json();

        if (!containerRef.current) return;

        // Create nodes dataset
        const nodes = new DataSet(
          data.nodes.map((node) => ({
            id: node.id,
            label: node.name,
            group: node.type,
            title: node.name,
            font: { size: 10, face: "Arial" },
            shape: node.type === "topic" ? "diamond" : "circle",
            color: node.type === "topic" ? "#ff7675" : "#74b9ff",
            size: node.type === "topic" ? 25 : 15,
            widthConstraint: { minimum: 80, maximum: 120 },
            heightConstraint: { minimum: 30, maximum: 60 },
          }))
        );

        // Create edges dataset
        const edges = new DataSet(
          data.edges.map((edge, index) => ({
            id: `edge-${index}`,
            from: edge.source,
            to: edge.target,
            arrows: "to",
            color: "#636e72",
            width: 2,
            title: edge.type,
          }))
        );

        // Network configuration
        const options = {
          nodes: {
            borderWidth: 2,
          },
          edges: {
            smooth: {
              enabled: true,
              type: "cubicBezier",
              roundness: 0.5,
              forceDirection: "horizontal",
            },
            length: 200,
            width: 2,
          },
          physics: {
            stabilization: false,
            hierarchicalRepulsion: {
              nodeDistance: 120,
              springLength: 200,
              springConstant: 0.01,
              damping: 0.09,
            },
            solver: "hierarchicalRepulsion",
          },
          interaction: {
            hover: true,
            tooltipDelay: 200,
          },
          layout: {
            improvedLayout: true,
            hierarchical: {
              enabled: true,
              direction: "DU",
              sortMethod: "directed",
              levelSeparation: 300,
              nodeSpacing: 100,
              treeSpacing: 100,
            },
          },
        };

        // Create and render the network
        const network = new Network(
          containerRef.current,
          { nodes, edges },
          options
        );
        networkRef.current = network;

        // Fit the network to the container
        network.fit();
      } catch (error) {
        console.error("Error loading graph data:", error);
      }
    };

    loadGraphData();

    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
      }
    };
  }, []);

  return (
    <div className="w-full h-screen">
      <div className="p-4">
        <h1 className="text-2xl font-bold mb-4">
          Political Party Standpoints Graph
        </h1>
        <p className="text-gray-600 mb-4">
          Interactive visualization of political party positions and standpoints
        </p>
      </div>
      <div
        ref={containerRef}
        className="w-full h-[calc(100vh-120px)] border border-gray-200 rounded-lg"
      />
    </div>
  );
}
