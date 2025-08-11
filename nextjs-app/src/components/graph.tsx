"use client";

import { useEffect, useRef } from "react";
import { Network } from "vis-network";
import { DataSet } from "vis-data";

const filename = "current_2025-08-10_20-13-36";

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
          data.nodes.map((node) => {
            let color, shape, size;

            switch (node.type) {
              case "topic":
                color = "#ff7675"; // Red for topics
                shape = "diamond";
                size = 25;
                break;
              case "argument":
                color = "#74b9ff"; // Blue for arguments
                shape = "circle";
                size = 18;
                break;
              case "fact":
                color = "#00b894"; // Green for facts
                shape = "circle";
                size = 16;
                break;
              case "value":
                color = "#fdcb6e"; // Yellow for values
                shape = "circle";
                size = 17;
                break;
              case "standpoint":
                color = "#a29bfe"; // Purple for standpoints
                shape = "circle";
                size = 19;
                break;
              default:
                color = "#fd79a8"; // Pink for unknown types
                shape = "circle";
                size = 15;
            }

            return {
              id: node.id,
              label: node.name,
              group: node.type,
              title: node.name,
              font: { size: 10, face: "Arial" },
              shape: shape,
              color: color,
              size: size,
              widthConstraint: { minimum: 80, maximum: 120 },
              heightConstraint: { minimum: 30, maximum: 60 },
            };
          })
        );

        // Create edges dataset
        const edges = new DataSet(
          data.edges.map((edge, index) => ({
            id: `edge-${index}`,
            from: edge.source,
            to: edge.target,
            title: edge.type,
          }))
        );

        // Identify root nodes (nodes with no incoming edges)
        const targetIds = new Set(data.edges.map((edge) => edge.target));
        const rootNodes = data.nodes.filter((node) => !targetIds.has(node.id));

        console.log(
          "Root nodes found:",
          rootNodes.map((n) => ({ id: n.id, name: n.name, type: n.type }))
        );
        console.log("Total nodes:", data.nodes.length);
        console.log("Total edges:", data.edges.length);

        // Network configuration
        const options = {
          nodes: {
            borderWidth: 2,
            margin: {
              top: 20,
              right: 20,
              bottom: 20,
              left: 20,
            },
            shadow: {
              enabled: true,
              color: "rgba(0,0,0,0.1)",
              size: 10,
              x: 5,
              y: 5,
            },
          },
          edges: {
            arrows: "to",
            smooth: {
              enabled: true,
              type: "cubicBezier",
              roundness: 0.1,
              forceDirection: "none",
            },
            length: 180,
            width: 1.2,
            color: {
              color: "#636e72",
              opacity: 0.7,
            },
            selectionWidth: 3,
            hoverWidth: 2.5,
          },
          physics: {
            enabled: true,
            stabilization: {
              enabled: true,
              iterations: 1000,
              updateInterval: 100,
            },
            forceAtlas2Based: {
              gravitationalConstant: -80,
              centralGravity: 0.005,
              springLength: 300,
              springConstant: 0.06,
              damping: 0.4,
              avoidOverlap: 0.8,
            },
            solver: "forceAtlas2Based",
            timestep: 0.35,
            adaptiveTimestep: true,
          },
          interaction: {
            hover: true,
            tooltipDelay: 200,
            zoomView: true,
            dragView: true,
            navigationButtons: true,
          },
          layout: {
            improvedLayout: true,
            hierarchical: {
              enabled: false,
            },
          },
          manipulation: {
            enabled: false,
          },
        };

        // Create and render the network
        const network = new Network(
          containerRef.current,
          { nodes, edges },
          options
        );
        networkRef.current = network;

        // Stop physics after stabilization to prevent continuous movement
        network.on("stabilizationProgress", (params) => {
          if (params.iterations >= params.total) {
            network.setOptions({ physics: { enabled: false } });
          }
        });

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
