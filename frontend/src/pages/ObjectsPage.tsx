import { useEffect, useState } from "react";
import { API_BASE_URL, fetchJson } from "../api";
import type { components } from "../types/api-generated";

type ProjectResponse = components["schemas"]["ProjectResponse"];
type BuildingResponse = components["schemas"]["BuildingResponse"];
type RevisionListItem = components["schemas"]["RevisionListItem"];
type ObjectListItem = components["schemas"]["ObjectListItem"];
type ObjectDetail = components["schemas"]["ObjectDetail"];

function ObjectsPage() {
  const [projects, setProjects] = useState<ProjectResponse[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");

  const [buildings, setBuildings] = useState<BuildingResponse[]>([]);
  const [selectedBuildingId, setSelectedBuildingId] = useState("");

  const [revisions, setRevisions] = useState<RevisionListItem[]>([]);
  const [selectedRevId, setSelectedRevId] = useState("");

  const [objects, setObjects] = useState<ObjectListItem[]>([]);
  const [selectedObjId, setSelectedObjId] = useState<string | null>(null);
  const [objectDetail, setObjectDetail] = useState<ObjectDetail | null>(null);

  const [isLoadingProjects, setIsLoadingProjects] = useState(true);
  const [isLoadingObjects, setIsLoadingObjects] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    async function loadProjects() {
      try {
        const data = await fetchJson<ProjectResponse[]>("/projects");
        setProjects(data);
        setSelectedProjectId(data.length > 0 ? data[0].project_id : "");
      } catch {
        setErrorMessage("Failed to fetch projects");
      } finally {
        setIsLoadingProjects(false);
      }
    }

    void loadProjects();
  }, []);

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
        setSelectedBuildingId(data.length > 0 ? data[0].building_id : "");
      } catch {
        setErrorMessage("Failed to fetch buildings");
      }
    }

    void loadBuildings();
  }, [selectedProjectId]);

  useEffect(() => {
    async function loadRevisions() {
      if (!selectedProjectId || !selectedBuildingId) {
        setRevisions([]);
        setSelectedRevId("");
        return;
      }
      try {
        const data = await fetchJson<RevisionListItem[]>(
          `/projects/${selectedProjectId}/buildings/${selectedBuildingId}/revisions`,
        );
        setRevisions(data);
        // Default to the latest revision (highest rev_number), per D40.
        const latest = data.reduce<RevisionListItem | null>(
          (best, current) =>
            best === null || current.rev_number > best.rev_number
              ? current
              : best,
          null,
        );
        setSelectedRevId(latest?.rev_id ?? "");
      } catch {
        setErrorMessage("Failed to fetch revisions");
      }
    }

    void loadRevisions();
  }, [selectedProjectId, selectedBuildingId]);

  useEffect(() => {
    async function loadObjects() {
      setSelectedObjId(null);
      setObjectDetail(null);

      if (!selectedProjectId || !selectedBuildingId || !selectedRevId) {
        setObjects([]);
        return;
      }

      setIsLoadingObjects(true);
      try {
        const data = await fetchJson<ObjectListItem[]>(
          `/projects/${selectedProjectId}/buildings/${selectedBuildingId}/revisions/${selectedRevId}/objects`,
        );
        setObjects(data);
      } catch {
        setErrorMessage("Failed to fetch objects");
      } finally {
        setIsLoadingObjects(false);
      }
    }

    void loadObjects();
  }, [selectedProjectId, selectedBuildingId, selectedRevId]);

  async function loadObjectDetail(objId: string) {
    setSelectedObjId(objId);
    setIsLoadingDetail(true);
    setErrorMessage("");

    try {
      const data = await fetchJson<ObjectDetail>(
        `/projects/${selectedProjectId}/buildings/${selectedBuildingId}/revisions/${selectedRevId}/objects/${objId}`,
      );
      setObjectDetail(data);
    } catch {
      setErrorMessage("Failed to fetch object detail");
    } finally {
      setIsLoadingDetail(false);
    }
  }

  return (
    <>
      <header className="page-header">
        <h1>AISIMS Objects</h1>
        <p className="page-subtitle">
          Browse objects across a project's buildings and revisions.
          Creation and editing happen via{" "}
          <a href={`${API_BASE_URL}/docs`}>{API_BASE_URL}/docs</a> - this
          view is read-only.
        </p>
      </header>

      <div className="selectors-row">
        <label className="selector">
          <span>Project</span>
          <select
            value={selectedProjectId}
            onChange={(event) => setSelectedProjectId(event.target.value)}
            disabled={isLoadingProjects || projects.length === 0}
          >
            {projects.map((project) => (
              <option key={project.project_id} value={project.project_id}>
                {project.project_name ?? project.project_id}
              </option>
            ))}
          </select>
        </label>

        <label className="selector">
          <span>Building</span>
          <select
            value={selectedBuildingId}
            onChange={(event) => setSelectedBuildingId(event.target.value)}
            disabled={buildings.length === 0}
          >
            {buildings.map((building) => (
              <option key={building.building_id} value={building.building_id}>
                {building.building_name ?? building.building_id}
              </option>
            ))}
          </select>
        </label>

        <label className="selector">
          <span>Revision</span>
          <select
            value={selectedRevId}
            onChange={(event) => setSelectedRevId(event.target.value)}
            disabled={revisions.length === 0}
          >
            {revisions.map((revision) => (
              <option key={revision.rev_id} value={revision.rev_id}>
                Rev {revision.rev_number}
              </option>
            ))}
          </select>
        </label>
      </div>

      {errorMessage && <p className="status-line is-error">{errorMessage}</p>}

      <div className="layout">
        <section className="panel">
          <div className="panel-head">
            <h2>Objects</h2>
            {objects.length > 0 && (
              <span className="count-chip">{objects.length} total</span>
            )}
          </div>

          {isLoadingObjects && (
            <p className="status-line">Loading objects...</p>
          )}
          {!isLoadingObjects && objects.length === 0 && (
            <p className="status-line">No objects in this revision.</p>
          )}

          {objects.length > 0 && (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Member ID</th>
                    <th>Stable ID</th>
                    <th>Type</th>
                    <th>Floor</th>
                    <th>Zone</th>
                    <th>Section</th>
                    <th>Material</th>
                    <th>Status</th>
                  </tr>
                </thead>

                <tbody>
                  {objects.map((obj) => (
                    <tr
                      key={obj.obj_id}
                      className={
                        selectedObjId === obj.obj_id ? "is-selected" : undefined
                      }
                    >
                      <td>
                        <button
                          type="button"
                          className="member-id-button"
                          onClick={() => void loadObjectDetail(obj.obj_id)}
                        >
                          {obj.obj_mark}
                        </button>
                      </td>
                      <td className="mono-cell">{obj.stable_id}</td>
                      <td>
                        <span className={`type-badge type-${obj.obj_type}`}>
                          {obj.obj_type}
                        </span>
                      </td>
                      <td>{obj.floor_name}</td>
                      <td>{obj.zone_label}</td>
                      <td>{obj.sect_label}</td>
                      <td>{obj.mat_name}</td>
                      <td>
                        <span
                          className={`status-badge status-${obj.change_status}`}
                        >
                          {obj.change_status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>

        <section className="panel">
          <div className="panel-head">
            <h2>Object Detail</h2>
          </div>

          {isLoadingDetail && (
            <p className="status-line">Loading detail...</p>
          )}

          {!isLoadingDetail && objectDetail === null && (
            <p className="detail-empty">Select an object from the table.</p>
          )}

          {!isLoadingDetail && objectDetail !== null && (
            <div className="detail-body">
              <div className="detail-title">
                <span className="member-id">{objectDetail.obj_mark}</span>
                <span className={`type-badge type-${objectDetail.obj_type}`}>
                  {objectDetail.obj_type}
                </span>
                <span
                  className={`status-badge status-${objectDetail.change_status}`}
                >
                  {objectDetail.change_status}
                </span>
              </div>

              <dl className="kv-grid">
                <div className="kv-cell">
                  <dt>Stable ID</dt>
                  <dd>{objectDetail.stable_id}</dd>
                </div>
                <div className="kv-cell">
                  <dt>Floor</dt>
                  <dd>{objectDetail.floor_name}</dd>
                </div>
                <div className="kv-cell">
                  <dt>Zone</dt>
                  <dd>{objectDetail.zone_label}</dd>
                </div>
                <div className="kv-cell">
                  <dt>Section</dt>
                  <dd>{objectDetail.sect_label}</dd>
                </div>
                <div className="kv-cell">
                  <dt>Material</dt>
                  <dd>{objectDetail.mat_name}</dd>
                </div>
              </dl>

              <div className="stat-row">
                <div className="stat">
                  <span className="stat-label">Qty. Section</span>
                  <span className="stat-value">
                    {objectDetail.quantity?.qty_sect ?? "-"}
                    {objectDetail.quantity && (
                      <span className="unit">m&sup3;/kg</span>
                    )}
                  </span>
                </div>
                <div className="stat">
                  <span className="stat-label">Qty. Bar</span>
                  <span className="stat-value">
                    {objectDetail.quantity?.qty_bar ?? "-"}
                    {objectDetail.quantity && <span className="unit">kg</span>}
                  </span>
                </div>
              </div>

              <div className="detail-section">
                <h3>Section Dimension</h3>
                <dl className="kv-grid">
                  {Object.entries(objectDetail.dimension).map(
                    ([field, value]) => (
                      <div className="kv-cell" key={field}>
                        <dt>{field}</dt>
                        <dd>{value}</dd>
                      </div>
                    ),
                  )}
                </dl>
              </div>

              <div className="detail-section">
                <h3>Geometry Points</h3>
                <table className="points-table">
                  <thead>
                    <tr>
                      <th>Point</th>
                      <th>X (mm)</th>
                      <th>Y (mm)</th>
                      <th>Z (mm)</th>
                    </tr>
                  </thead>

                  <tbody>
                    {objectDetail.geometry_points.map((point, index) => (
                      <tr key={`${objectDetail.obj_id}-point-${index}`}>
                        <td>P{index + 1}</td>
                        <td>{point[0]}</td>
                        <td>{point[1]}</td>
                        <td>{point[2]}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="detail-section">
                <h3>Reinforcement</h3>
                {objectDetail.reinforcements.length === 0 ? (
                  <p className="status-line">No reinforcement rows.</p>
                ) : (
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>Bar Spec</th>
                          <th>Dia (mm)</th>
                          <th>Grade</th>
                          <th>Role</th>
                          <th>Count</th>
                          <th>Length (mm)</th>
                          <th>Spacing (mm)</th>
                          <th>Hook</th>
                        </tr>
                      </thead>

                      <tbody>
                        {objectDetail.reinforcements.map((bar) => (
                          <tr key={bar.bar_id}>
                            <td>{bar.barspec_label}</td>
                            <td>{bar.barspec_dia}</td>
                            <td>{bar.barspec_grade}</td>
                            <td>{bar.bar_role}</td>
                            <td>{bar.bar_count}</td>
                            <td>{bar.bar_len}</td>
                            <td>{bar.bar_space ?? "-"}</td>
                            <td>{bar.bar_hook_type ?? "-"}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            </div>
          )}
        </section>
      </div>
    </>
  );
}

export default ObjectsPage;
