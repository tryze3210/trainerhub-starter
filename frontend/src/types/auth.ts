export type UserRole = "customer" | "trainer" | "admin";

export type AuthUser = {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role: UserRole;
};

export type LoginResponse = {
  access: string;
  refresh: string;
  user: AuthUser;
};
