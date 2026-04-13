export async function fetchMyEnrollments(client: any) {
  return client.get('/api/v1/cohorts/me/enrollments/');
}

export async function fetchTrainerCohorts(client: any) {
  return client.get('/api/v1/cohorts/me/cohorts/');
}

export async function fetchCohortDashboard(client: any, cohortId: string) {
  return client.get(`/api/v1/cohorts/cohorts/${cohortId}/dashboard/`);
}
