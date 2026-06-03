import { Badge } from "@/components/ui/Badge";
import { CAMPAIGN_STATUS_COLOR, CAMPAIGN_STATUS_LABEL, CampaignStatus, isCampaignRunning } from "@/lib/types";

export function CampaignStatusBadge({ status }: { status: CampaignStatus }) {
  return (
    <Badge
      label={CAMPAIGN_STATUS_LABEL[status]}
      colorClass={CAMPAIGN_STATUS_COLOR[status]}
      pulse={isCampaignRunning(status)}
    />
  );
}
