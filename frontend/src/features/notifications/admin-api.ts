import { apiClient } from "@/shared/api/client";

export async function getNotificationDeliveryOverview() {
  const { data } = await apiClient.get("/api/v1/notifications/admin/deliveries/overview/");
  return data;
}

export async function getNotificationDeliveries(params: Record<string, string> = {}) {
  const { data } = await apiClient.get("/api/v1/notifications/admin/deliveries/", { params });
  return data;
}

export async function getNotificationTemplates() {
  const { data } = await apiClient.get("/api/v1/notifications/admin/templates/");
  return data;
}
