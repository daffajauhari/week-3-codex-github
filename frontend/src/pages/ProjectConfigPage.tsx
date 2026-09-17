import { useEffect, useMemo, useState } from "react";
import { fetchJson } from "../api";
import type { components } from "../types/api-generated";

type ProjectResponse = components["schemas"]["ProjectResponse"];
type BuildingResponse = components["schemas"]["BuildingResponse"];

type EntityScope = "none" | "project" | "building";

type EntityKey =
  | "projects"
  | "buildings"
  | "floors"
  | "zones"
  | "grid"
  | "materials"
  | "sections"
  | "barspec";

interface EntityConfig {
  key: EntityKey;
  label: string;
  scope: EntityScope;
  path: (projectId: string, buildingId: string) => string;
}

const ENTITY_CONFIGS: EntityConfig[] = [
  {
    key: "projects",
    label: "Projects",
    scope: "none",
    path: () => "/projects",
  },
  {
    key: "buildings",
    label: "Buildings",
    scope: "project",
    path: (projectId) => `/projects/${projectId}/buildings`,
  },
  {
    key: "floors",
    label: "Floors",
    scope: "building",
    path: (projectId, buildingId) =>
      `/projects/${projectId}/buildings/${buildingId}/floors`,
  },
  {
    key: "zones",
    label: "Zones",
    scope: "building",
    path: (projectId, buildingId) =>
      `/projects/${projectId}/buildings/${buildingId}/zones`,
  },
  {
    key: "grid",
    label: "Grid",
    scope: "building",
    path: (projectId, buildingId) =>
      `/projects/${projectId}/buildings/${buildingId}/grid`,
  },
  {
    key: "materials",
    label: "Materials",
    scope: "none",
    path: () => "/materials",
  },
  {
    key: "sections",
    label: "Sections",
    scope: "none",
    path: () => "/sections",
  },
  {
    key: "barspec",
    label: "Bar Specs",
    scope: "none",
    path: () => "/barspec",
  },
];

type Row = Record<string, unknown>;

function formatCell(value: unknown): string {
  if (value === null || value === undefined) return "-";
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}

function ProjectConfigPage() {
  const [entityKey, setEntityKey] = useState<EntityKey>("projects");

  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");

  const [buildings, setBuildings] = useState<BuildingResponse[]>([]);
  const [selectedBuildingId, setSelectedBuildingId] = useState("");

  const [rows, setRows] = useState<Row[]>([]);
  const [isLoadingRows, setIsLoadingRows] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  const config = useMemo(
    () =>
      ENTITY_CONFIGS.find((entity) => entity.key === entityKey) ??
      ENTITY_CONFIGS[0],
    [entityKey],
  );

  useEffect(() => {
    async function loadProjects() {
      try {
        const data = await fetchJson<ProjectResponse[]>("/projects");
        setProjects(data);
        setSelectedProjectId((current) =>
          current || (data.length > 0 ? data[0].project_id : ""),
        );
      } catch {
        setErrorMessage("Failed to fetch projects");
      }
    }

    if (config.scope !== "none") {
      void loadProjects();
    }
  }, [config.scope]);

  useEffect(() => {
    async function loadBuildings() {
      if (!selectedProjectId) {
        setBuildings([]);
        setSelectedBuildingId("");
        return;
      }
      try {
        const data = await fetchJson<BuildingResponse[]>(
          `/projects/${selectedProjectId}/buildings`,
        );
        setBuildings(data);
        setSelectedBuildingId((current) =>
          data.some((building) => building.building_id === current)
            ? current
            : data.length > 0
              ? data[0].building_id
              : "",
        );
      } catch {
        setErrorMessage("Failed to fetch buildings");
      }
    }

    if (config.scope === "building") {
      void loadBuildings();
    }
  }, [config.scope, selectedProjectId]);

  useEffect(() => {
    async function loadRows() {
      if (config.scope === "project" && !selectedProjectId) {
        setRows([]);
        return;
      }
      if (
        config.scope === "building" &&
        (!selectedProjectId || !selectedBuildingId)
      ) {
        setRows([]);
        return;
      }

      setIsLoadingRows(true);
      setErrorMessage("");
      try {
        const data = await fetchJson<Row[]>(
          config.path(selectedProjectId, selectedBuildingId),
        );
        setRows(data);
      } catch {
        setErrorMessage(`Failed to fetch ${config.label.toLowerCase()}`);
        setRows([]);
      } finally {
        setIsLoadingRows(false);
      }
    }

    void loadRows();
  }, [config, selectedProjectId, selectedBuildingId]);

  const columns = rows.length > 0 ? Object.keys(rows[0]) : [];

  return (
    <>
      <header className="page-header">
        <h1>AISIMS Project Configuration</h1>
        <p className="page-subtitle">
          Browse Project Configuration entities - pick an entity below to
          view its rows.
        </p>
      </header>

      <div className="selectors-row">
        <label className="selector">
          <span>Entity</span>
          <select
            value={entityKey}
            onChange={(event) => setEntityKey(event.target.value as EntityKey)}
          >
            {ENTITY_CONFIGS.map((entity) => (
              <option key={entity.key} value={entity.key}>
                {entity.label}
              </option>
            ))}
          </select>
        </label>

        {config.scope !== "none" && (
          <label className="selector">
            <span>Project</span>
            <select
              value={selectedProjectId}
              onChange={(event) => setSelectedProjectId(event.target.value)}
              disabled={projects.length === 0}
            >
              {projects.map((project) => (
                <option key={project.project_id} value={project.project_id}>
                  {project.project_name ?? project.project_id}
                </option>
              ))}
            </select>
          </label>
        )}

        {config.scope === "building" && (
          <label className="selector">
            <span>Building</span>
            <select
              value={selectedBuildingId}
              onChange={(event) => setSelectedBuildingId(event.target.value)}
              disabled={buildings.length === 0}
            >
              {buildings.map((building) => (
                <option
                  key={building.building_id}
                  value={building.building_id}
                >
                  {building.building_name ?? building.building_id}
                </option>
              ))}
            </select>
          </label>
        )}
      </div>

      {errorMessage && <p className="status-line is-error">{errorMessage}</p>}

      <section className="panel">
        <div className="panel-head">
          <h2>{config.label}</h2>
          {rows.length > 0 && (
            <span className="count-chip">{rows.length} total</span>
          )}
        </div>

        {isLoadingRows && <p className="status-line">Loading...</p>}
        {!isLoadingRows && rows.length === 0 && !errorMessage && (
          <p className="status-line">No rows found.</p>
        )}

        {!isLoadingRows && rows.length > 0 && (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  {columns.map((column) => (
                    <th key={column}>{column}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((row, index) => (
                  <tr key={index}>
                    {columns.map((column) => (
                      <td key={column} className="mono-cell">
                        {formatCell(row[column])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}

export default ProjectConfigPage;
