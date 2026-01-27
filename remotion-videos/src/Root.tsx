import { Composition } from 'remotion';
import { HeroWorkflow } from './Compositions/HeroWorkflow';
import { RAGPipeline } from './Compositions/RAGPipeline';
import { Observability } from './Compositions/Observability';
import { NodeLibrary } from './Compositions/NodeLibrary';
import { MultiAgent } from './Compositions/MultiAgent';

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="HeroWorkflow"
        component={HeroWorkflow}
        durationInFrames={450}
        fps={30}
        width={1920}
        height={1080}
      />
      <Composition
        id="RAGPipeline"
        component={RAGPipeline}
        durationInFrames={360}
        fps={30}
        width={1280}
        height={960}
      />
      <Composition
        id="Observability"
        component={Observability}
        durationInFrames={300}
        fps={30}
        width={1280}
        height={960}
      />
      <Composition
        id="MultiAgent"
        component={MultiAgent}
        durationInFrames={300}
        fps={30}
        width={1280}
        height={960}
      />
      <Composition
        id="NodeLibrary"
        component={NodeLibrary}
        durationInFrames={240}
        fps={30}
        width={1280}
        height={960}
      />
    </>
  );
};
