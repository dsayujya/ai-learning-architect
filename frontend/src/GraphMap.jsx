import React, { useMemo } from 'react';
import { ReactFlow, Controls, Background, Handle, Position } from '@xyflow/react';
import '@xyflow/react/dist/style.css';

const CustomNode = ({ data, selected }) => {
  let statusClass = '';
  if (data.isCompleted) statusClass = 'completed';
  else if (data.priority === 'Critical') statusClass = 'critical';

  const hasVideo = data.youtube_id != null;
  const videoUrl = hasVideo ? `https://www.youtube.com/embed/${data.youtube_id}` : null;

  return (
    <div style={{ position: 'relative' }}>
      <Handle type="target" position={Position.Top} style={{ background: '#38bdf8', width: 12, height: 12, border: '2px solid rgba(30, 41, 59, 1)' }} />
      <div className={`rich-node-card ${statusClass} ${selected ? 'selected' : ''}`}>
        <div className="node-info-col">
          <div className="node-step">Step {data.order}</div>
          <div className="node-title" style={{ fontSize: '1.25rem', fontWeight: '800' }}>{data.topic}</div>
          <div style={{ fontSize: '0.85rem', color: '#94a3b8', marginTop: 4 }}>
            Priority: <span style={{ color: statusClass === 'critical' ? '#f59e0b' : '#38bdf8' }}>{data.priority}</span>
          </div>
          {data.confidence != null && (
            <div style={{
              fontSize: '0.75rem',
              color: '#a78bfa',
              marginTop: 4,
              fontFamily: 'monospace'
            }}>
              GNN Readiness: {(data.confidence * 100).toFixed(1)}%
            </div>
          )}
        </div>

        <div className="node-video-col nodrag">
          {hasVideo ? (
            <iframe
              width="350"
              height="200"
              src={videoUrl}
              title={`${data.topic} Video Player`}
              frameBorder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
              allowFullScreen
              style={{ border: 'none', display: 'block', pointerEvents: 'auto' }}
            ></iframe>
          ) : (
            <div style={{
              width: 350,
              height: 200,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(30, 41, 59, 0.6)',
              borderRadius: 8,
              color: '#64748b',
              fontSize: '0.9rem'
            }}>
              No video available
            </div>
          )}
        </div>
      </div>
      <Handle type="source" position={Position.Bottom} style={{ background: '#38bdf8', width: 12, height: 12, border: '2px solid rgba(30, 41, 59, 1)' }} />
    </div>
  );
};

const nodeTypes = { custom: CustomNode };

export default function GraphMap({ roadmap }) {
  const initialNodes = useMemo(() => {
    return roadmap.map((step, index) => ({
      id: `node-${step.order}`,
      type: 'custom',
      position: { x: step.x, y: step.y },
      data: {
        topic: step.topic,
        order: step.order,
        priority: step.priority,
        isCompleted: step.prerequisites_met,
        youtube_id: step.youtube_id,
        confidence: step.confidence,
        relevance_score: step.relevance_score
      }
    }));
  }, [roadmap]);

  const initialEdges = useMemo(() => {
    const edges = [];
    for (let i = 0; i < roadmap.length - 1; i++) {
      edges.push({
        id: `edge-${roadmap[i].order}-${roadmap[i + 1].order}`,
        source: `node-${roadmap[i].order}`,
        target: `node-${roadmap[i + 1].order}`,
        animated: true,
        style: { stroke: '#38bdf8', strokeWidth: 2 }
      })
    }
    return edges;
  }, [roadmap]);

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={initialNodes}
        edges={initialEdges}
        nodeTypes={nodeTypes}
        fitView
      >
        <Background color="#334155" gap={24} />
        <Controls className="custom-controls" />
      </ReactFlow>
    </div>
  );
}
