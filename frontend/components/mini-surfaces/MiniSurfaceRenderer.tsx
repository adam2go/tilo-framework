import { getMiniSurfaceRegistration, type MiniSurfaceType } from "./registry";

export function MiniSurfaceRenderer({
  props,
  surfaceType,
}: {
  props: Record<string, unknown>;
  surfaceType: MiniSurfaceType;
}) {
  const registration = getMiniSurfaceRegistration(surfaceType);
  const Component = registration.component;
  return <Component {...props} />;
}
