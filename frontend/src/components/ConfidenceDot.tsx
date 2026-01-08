import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import { ConfidenceLevel } from "@/types/extraction";

interface ConfidenceDotProps {
  confidence: number;
}

const getConfidenceLevel = (confidence: number): ConfidenceLevel => {
  if (confidence >= 0.8) return 'high';
  if (confidence >= 0.6) return 'medium';
  return 'low';
};

const ConfidenceDot = ({ confidence }: ConfidenceDotProps) => {
  const level = getConfidenceLevel(confidence);
  
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <span className={`confidence-dot confidence-${level}`} />
      </TooltipTrigger>
      <TooltipContent side="left" className="text-xs">
        Confidence: {confidence.toFixed(2)}
      </TooltipContent>
    </Tooltip>
  );
};

export default ConfidenceDot;
