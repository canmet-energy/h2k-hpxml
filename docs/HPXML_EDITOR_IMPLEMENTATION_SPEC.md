# High-Level Implementation Specification
## HPXML Building Editor with Component Navigator

**Version:** 1.1
**Date:** January 2025
**Project:** H2K-HPXML Translation Tool
**Document Type:** Technical Specification

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Technology Stack Recommendations](#2-technology-stack-recommendations)
3. [Data Model](#3-data-model)
4. [Component Architecture](#4-component-architecture)
5. [State Management](#5-state-management)
6. [HPXML Parser & Serializer](#6-hpxml-parser--serializer)
7. [Validation System](#7-validation-system)
8. [Tree Builder Service](#8-tree-builder-service)
9. [Component Templates](#9-component-templates)
10. [File Operations](#10-file-operations)
11. [Undo/Redo System](#11-undoredo-system)
12. [Testing Strategy](#12-testing-strategy)
13. [Performance Optimization](#13-performance-optimization)
14. [Deployment](#14-deployment)
15. [User Documentation](#15-user-documentation)
16. [Development Phases](#16-development-phases)
17. [Success Metrics](#17-success-metrics)

---

## 1. Architecture Overview

### 1.1 System Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    PRESENTATION LAYER                    │
├──────────────────────┬──────────────────────────────────┤
│  Tree Navigator      │     Properties Panel             │
│  Component           │     Component                    │
├──────────────────────┴──────────────────────────────────┤
│              APPLICATION LAYER                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  State Mgmt │  │  Validation │  │   Actions   │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
├──────────────────────────────────────────────────────────┤
│              DATA LAYER                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  HPXML      │  │  XSD Schema │  │  Templates  │    │
│  │  Parser     │  │  Validator  │  │  Library    │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└──────────────────────────────────────────────────────────┘
```

### 1.2 Design Patterns

- **MVC/MVVM**: Separate data, view, and logic
- **Observer Pattern**: For tree-properties synchronization
- **Command Pattern**: For undo/redo functionality
- **Factory Pattern**: For creating HPXML components
- **Strategy Pattern**: For different validation rules
- **Composite Pattern**: For tree structure

### 1.3 UI Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│ File   Edit   View   Tools   Validate   Help                        │
├──────────────┬──────────────────────────────────────────────────────┤
│              │                                                       │
│  BUILDING    │              PROPERTIES PANEL                         │
│  NAVIGATOR   │                                                       │
│              │                                                       │
│  [Tree View] │            [Component Details]                        │
│              │                                                       │
│   30%        │                   70%                                 │
│              │                                                       │
└──────────────┴──────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack Recommendations

### 2.1 Desktop Application Options

#### Option A: Electron + Web Technologies (Recommended)
```
Frontend:   React/Vue/Svelte
State:      Redux/MobX/Zustand
UI Library: Material-UI/Ant Design/Tailwind
XML Parser: xml2js/fast-xml-parser
Validation: lxml (Python bridge) or ajv
```

**Pros:**
- Cross-platform (Windows, macOS, Linux)
- Rich UI component libraries
- Easy deployment and updates
- Large developer ecosystem

**Cons:**
- Larger file size
- Higher memory usage

#### Option B: Python Desktop (Qt/wxPython)
```
Framework:  PyQt6/PySide6 or wxPython
XML:        lxml (already used in validator)
Tree:       QTreeWidget/wx.TreeCtrl
Forms:      Dynamic form generation
```

**Pros:**
- Native integration with existing Python validator
- Better performance for large files
- Smaller memory footprint

**Cons:**
- UI development slower
- Limited modern UI components

#### Option C: Web Application
```
Backend:    FastAPI/Flask (Python)
Frontend:   React/Vue
Database:   PostgreSQL (for multi-user)
Deployment: Docker/Cloud
```

**Pros:**
- Multi-user support
- No installation needed
- Centralized validation

**Cons:**
- Requires server infrastructure
- Network dependency

**Recommendation: Option A (Electron + React)** for balance of features and development speed.

---

## 3. Data Model

### 3.1 Core Data Structures

#### HPXML Document Model
```typescript
interface HPXMLDocument {
  schemaVersion: string;
  metadata: TransactionHeader;
  buildings: Building[];
  filePath?: string;
  modified: boolean;
  validationState: ValidationState;
}

interface Building {
  id: string;
  buildingID: string;
  siteInfo: SiteInfo;
  climate: ClimateInfo;
  occupancy: OccupancyInfo;
  construction: ConstructionInfo;
  enclosure: Enclosure;
  systems: Systems;
  appliances: Appliances;
  lighting: Lighting;
  miscLoads: MiscLoads;
}
```

#### Component Base
```typescript
interface HPXMLComponent {
  systemIdentifier: string;
  type: ComponentType;
  properties: Record<string, any>;
  references: ComponentReference[];
  validation: ComponentValidation;
  extensions?: Record<string, any>;
}

interface ComponentReference {
  propertyName: string;  // e.g., "AttachedToWall"
  targetId: string;       // e.g., "Wall1"
  targetType: string;     // e.g., "Wall"
  valid: boolean;
}

enum ComponentType {
  WALL = "Wall",
  WINDOW = "Window",
  DOOR = "Door",
  ROOF = "Roof",
  FOUNDATION = "Foundation",
  HEATING_SYSTEM = "HeatingSystem",
  COOLING_SYSTEM = "CoolingSystem",
  // ... etc
}
```

#### Tree Node Model
```typescript
interface TreeNode {
  id: string;
  label: string;
  icon: string;
  type: NodeType;
  componentId?: string;
  children?: TreeNode[];
  expanded: boolean;
  selected: boolean;
  validationState: ValidationLevel;
  metadata?: Record<string, any>;
}

enum NodeType {
  ROOT = "root",
  CATEGORY = "category",
  COMPONENT = "component",
  REFERENCE = "reference"
}

enum ValidationLevel {
  VALID = "valid",
  WARNING = "warning",
  ERROR = "error",
  UNKNOWN = "unknown"
}
```

### 3.2 View Models

#### Building Component View Transformer
```typescript
interface ComponentViewModel {
  // Logical grouping
  logicalParent: string;
  physicalParent: string;
  attachments: ComponentViewModel[];

  // Display
  displayName: string;
  summary: string;
  icon: string;

  // Interaction
  editable: boolean;
  deletable: boolean;
  duplicable: boolean;
}
```

---

## 4. Component Architecture

### 4.1 Main Application Structure

```
src/
├── main/
│   ├── index.ts                    # Electron main process
│   ├── menu.ts                     # Application menu
│   ├── file-handlers.ts            # File open/save
│   └── ipc-handlers.ts             # IPC communication
│
├── renderer/
│   ├── app.tsx                     # Root component
│   ├── store/
│   │   ├── store.ts                # Redux/state store
│   │   ├── slices/
│   │   │   ├── document-slice.ts   # HPXML document state
│   │   │   ├── ui-slice.ts         # UI state
│   │   │   └── validation-slice.ts # Validation state
│   │   └── actions/
│   │       ├── document-actions.ts
│   │       └── component-actions.ts
│   │
│   ├── components/
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx       # Main 2-pane layout
│   │   │   ├── MenuBar.tsx
│   │   │   └── StatusBar.tsx
│   │   │
│   │   ├── navigator/
│   │   │   ├── TreeNavigator.tsx   # Left pane
│   │   │   ├── TreeNode.tsx
│   │   │   ├── TreeToolbar.tsx
│   │   │   ├── SearchBox.tsx
│   │   │   └── ContextMenu.tsx
│   │   │
│   │   ├── properties/
│   │   │   ├── PropertiesPanel.tsx # Right pane
│   │   │   ├── PropertyForm.tsx
│   │   │   ├── TabContainer.tsx
│   │   │   └── fields/
│   │   │       ├── TextField.tsx
│   │   │       ├── SelectField.tsx
│   │   │       ├── NumberField.tsx
│   │   │       └── ReferenceField.tsx
│   │   │
│   │   ├── forms/
│   │   │   ├── WallForm.tsx
│   │   │   ├── WindowForm.tsx
│   │   │   ├── HeatingSystemForm.tsx
│   │   │   └── [... component-specific forms]
│   │   │
│   │   └── dialogs/
│   │       ├── AddComponentDialog.tsx
│   │       ├── DeleteConfirmDialog.tsx
│   │       ├── ValidationDialog.tsx
│   │       └── AboutDialog.tsx
│   │
│   ├── services/
│   │   ├── hpxml-parser.ts         # XML parsing
│   │   ├── hpxml-serializer.ts     # XML generation
│   │   ├── validator.ts            # Python validator bridge
│   │   ├── tree-builder.ts         # Build tree from HPXML
│   │   └── template-service.ts     # Component templates
│   │
│   ├── utils/
│   │   ├── calculations.ts         # R-value, etc.
│   │   ├── units.ts                # Unit conversions
│   │   └── helpers.ts
│   │
│   └── types/
│       ├── hpxml-types.ts
│       ├── tree-types.ts
│       └── ui-types.ts
│
└── python/
    ├── validator_bridge.py         # Python-JS bridge
    └── hpxml_validator.py          # Existing validator
```

### 4.2 Key Components

#### TreeNavigator Component
```typescript
interface TreeNavigatorProps {
  document: HPXMLDocument;
  selectedNode: string | null;
  onNodeSelect: (nodeId: string) => void;
  onNodeExpand: (nodeId: string, expanded: boolean) => void;
  onNodeAdd: (parentId: string, type: ComponentType) => void;
  onNodeDelete: (nodeId: string) => void;
  onNodeDuplicate: (nodeId: string) => void;
}

const TreeNavigator: React.FC<TreeNavigatorProps> = ({
  document,
  selectedNode,
  onNodeSelect,
  // ...
}) => {
  const treeData = useTreeBuilder(document);
  const [searchTerm, setSearchTerm] = useState('');
  const [filter, setFilter] = useState<FilterOptions>(defaultFilter);

  // Render tree with search/filter
  // Handle context menu
  // Handle drag-drop (future)

  return (
    <div className="tree-navigator">
      <TreeToolbar
        onAdd={handleAdd}
        onDelete={handleDelete}
        onSearch={setSearchTerm}
      />
      <Tree
        data={treeData}
        selected={selectedNode}
        onSelect={onNodeSelect}
        filter={filter}
        searchTerm={searchTerm}
      />
    </div>
  );
};
```

#### PropertiesPanel Component
```typescript
interface PropertiesPanelProps {
  component: HPXMLComponent | null;
  onChange: (updates: Partial<HPXMLComponent>) => void;
  onValidate: () => void;
  readOnly?: boolean;
}

const PropertiesPanel: React.FC<PropertiesPanelProps> = ({
  component,
  onChange,
  onValidate
}) => {
  const [activeTab, setActiveTab] = useState('general');
  const [localChanges, setLocalChanges] = useState({});

  if (!component) {
    return <EmptyState message="Select a component" />;
  }

  const FormComponent = getFormForType(component.type);

  return (
    <div className="properties-panel">
      <PanelHeader
        component={component}
        onSave={handleSave}
        onCancel={handleCancel}
      />
      <TabContainer
        tabs={getTabsForType(component.type)}
        active={activeTab}
        onChange={setActiveTab}
      />
      <FormComponent
        data={component.properties}
        onChange={handleChange}
        validation={component.validation}
      />
      <ValidationSummary validation={component.validation} />
    </div>
  );
};
```

#### Dynamic Form Generator
```typescript
interface FormField {
  name: string;
  label: string;
  type: 'text' | 'number' | 'select' | 'reference' | 'boolean';
  required: boolean;
  validation?: ValidationRule[];
  options?: SelectOption[];
  units?: string;
  help?: string;
}

interface FormSchema {
  title: string;
  tabs: FormTab[];
}

interface FormTab {
  id: string;
  label: string;
  fields: FormField[];
}

const DynamicForm: React.FC<{
  schema: FormSchema;
  data: Record<string, any>;
  onChange: (field: string, value: any) => void;
}> = ({ schema, data, onChange }) => {
  return (
    <form>
      {schema.tabs.map(tab => (
        <TabPanel key={tab.id}>
          {tab.fields.map(field => (
            <FormField
              key={field.name}
              field={field}
              value={data[field.name]}
              onChange={(v) => onChange(field.name, v)}
            />
          ))}
        </TabPanel>
      ))}
    </form>
  );
};
```

---

## 5. State Management

### 5.1 Redux Store Structure

```typescript
interface RootState {
  document: DocumentState;
  ui: UIState;
  validation: ValidationState;
  history: HistoryState;
}

interface DocumentState {
  current: HPXMLDocument | null;
  filePath: string | null;
  modified: boolean;
  autoSaveEnabled: boolean;
  lastSaved: Date | null;
}

interface UIState {
  selectedComponent: string | null;
  expandedNodes: Set<string>;
  activeTab: string;
  searchTerm: string;
  filter: FilterOptions;
  layout: LayoutConfig;
}

interface ValidationState {
  validationResults: Map<string, ValidationResult>;
  lastValidation: Date | null;
  autoValidate: boolean;
}

interface HistoryState {
  past: DocumentSnapshot[];
  future: DocumentSnapshot[];
  maxHistory: number;
}
```

### 5.2 Key Actions

```typescript
// Document Actions
const documentActions = {
  loadDocument: (filePath: string) => {},
  saveDocument: (filePath?: string) => {},
  updateComponent: (componentId: string, updates: any) => {},
  addComponent: (parentId: string, type: ComponentType, data: any) => {},
  deleteComponent: (componentId: string) => {},
  duplicateComponent: (componentId: string) => {},
};

// UI Actions
const uiActions = {
  selectComponent: (componentId: string) => {},
  expandNode: (nodeId: string, expanded: boolean) => {},
  setActiveTab: (tabId: string) => {},
  updateSearch: (term: string) => {},
  updateFilter: (filter: FilterOptions) => {},
};

// Validation Actions
const validationActions = {
  validateComponent: (componentId: string) => {},
  validateDocument: () => {},
  clearValidation: () => {},
};

// History Actions
const historyActions = {
  undo: () => {},
  redo: () => {},
  createSnapshot: () => {},
};
```

---

## 6. HPXML Parser & Serializer

### 6.1 Parser Service

```typescript
class HPXMLParser {
  parse(xmlString: string): HPXMLDocument {
    // Parse XML to JS object
    const xmlObj = this.parseXMLString(xmlString);

    // Transform to internal model
    const document = this.transformToDocument(xmlObj);

    // Build component index
    this.buildComponentIndex(document);

    // Validate references
    this.validateReferences(document);

    return document;
  }

  private parseXMLString(xml: string): any {
    // Use xml2js or fast-xml-parser
    return xmlParser.parse(xml, {
      ignoreAttributes: false,
      attributeNamePrefix: "@",
      parseAttributeValue: true
    });
  }

  private transformToDocument(xmlObj: any): HPXMLDocument {
    // Map XML structure to internal model
    // Handle HPXML v4.0 namespace
    // Extract all components
    // Build relationships
  }

  private buildComponentIndex(doc: HPXMLDocument): void {
    // Create map of systemIdentifier -> component
    // For fast lookups and reference validation
  }
}
```

### 6.2 Serializer Service

```typescript
class HPXMLSerializer {
  serialize(document: HPXMLDocument): string {
    // Transform internal model to XML structure
    const xmlObj = this.transformToXML(document);

    // Add namespace and schema version
    this.addNamespace(xmlObj);

    // Serialize to XML string
    const xmlString = this.buildXMLString(xmlObj);

    // Format/prettify
    return this.formatXML(xmlString);
  }

  private transformToXML(doc: HPXMLDocument): any {
    // Reverse of parser transformation
    // Ensure proper HPXML structure
    // Maintain element order per schema
  }

  private addNamespace(xmlObj: any): void {
    xmlObj["@_xmlns"] = "http://hpxmlonline.com/2023/09";
    xmlObj["@_schemaVersion"] = "4.0";
  }

  private buildXMLString(xmlObj: any): string {
    const builder = new XMLBuilder({
      format: true,
      ignoreAttributes: false,
      attributeNamePrefix: "@_"
    });
    return builder.build(xmlObj);
  }
}
```

---

## 7. Validation System

### 7.1 Multi-Layer Validation

```typescript
interface ValidationSystem {
  // Layer 1: Field-level validation (immediate)
  validateField(field: FormField, value: any): FieldValidation;

  // Layer 2: Component-level validation (on change)
  validateComponent(component: HPXMLComponent): ComponentValidation;

  // Layer 3: Document-level validation (on demand)
  validateDocument(document: HPXMLDocument): DocumentValidation;

  // Layer 4: XSD schema validation (via Python)
  validateAgainstSchema(xmlString: string): SchemaValidation;
}
```

### 7.2 Validation Rules

```typescript
interface ValidationRule {
  name: string;
  level: ValidationLevel;
  check: (value: any, context?: any) => boolean;
  message: string;
  suggestion?: string;
}

// Example rules
const wallValidationRules: ValidationRule[] = [
  {
    name: "area_positive",
    level: ValidationLevel.ERROR,
    check: (v) => v > 0,
    message: "Area must be greater than 0",
  },
  {
    name: "rvalue_positive",
    level: ValidationLevel.ERROR,
    check: (v) => v > 0,
    message: "R-Value must be greater than 0",
  },
  {
    name: "rvalue_minimum",
    level: ValidationLevel.WARNING,
    check: (v) => v >= 13,
    message: "R-Value below code minimum (R-13)",
    suggestion: "Consider increasing insulation"
  },
  {
    name: "solar_absorptance_range",
    level: ValidationLevel.ERROR,
    check: (v) => v >= 0 && v <= 1,
    message: "Solar absorptance must be between 0 and 1",
  }
];
```

### 7.3 Python Validator Bridge

```typescript
class PythonValidatorBridge {
  async validateXML(xmlString: string): Promise<ValidationResult> {
    // Call Python validator via child_process or pyodide

    const pythonScript = `
from h2k_hpxml.utils.hpxml_validator import validate_hpxml
import sys
import json

result = validate_hpxml('${tempFilePath}')
output = {
  'valid': result.is_valid,
  'errors': [{'line': e.line, 'message': e.message} for e in result.errors]
}
print(json.dumps(output))
`;

    const result = await this.executePython(pythonScript);
    return this.parseValidationResult(result);
  }

  private async executePython(script: string): Promise<string> {
    // Option 1: spawn Python process
    // Option 2: use Pyodide (Python in WASM)
    // Option 3: REST API to Python backend
  }
}
```

---

## 8. Tree Builder Service

### 8.1 Building Component View

```typescript
class TreeBuilder {
  buildComponentTree(document: HPXMLDocument): TreeNode[] {
    const building = document.buildings[0];

    return [
      this.createRootNode(building),
      this.createSiteNode(building.siteInfo),
      this.createClimateNode(building.climate),
      this.createOccupancyNode(building.occupancy),
      this.createConstructionNode(building.construction),
      this.createInfiltrationNode(building.enclosure.airInfiltration),
      this.createWallsNode(building.enclosure),
      this.createFoundationsNode(building.enclosure),
      this.createAtticsNode(building.enclosure),
      this.createHVACNode(building.systems),
      this.createVentilationNode(building.systems),
      this.createWaterHeatingNode(building.systems),
      this.createAppliancesNode(building.appliances),
      this.createLightingNode(building.lighting),
      this.createMiscLoadsNode(building.miscLoads)
    ];
  }

  private createWallsNode(enclosure: Enclosure): TreeNode {
    const walls = enclosure.walls || [];

    return {
      id: 'walls-group',
      label: `Above-Grade Walls (${walls.length})`,
      icon: '🧱',
      type: NodeType.CATEGORY,
      expanded: true,
      children: walls.map(wall => this.createWallNode(wall, enclosure))
    };
  }

  private createWallNode(wall: Wall, enclosure: Enclosure): TreeNode {
    // Find windows and doors attached to this wall
    const attachedWindows = (enclosure.windows || [])
      .filter(w => w.attachedToWall === wall.systemIdentifier);
    const attachedDoors = (enclosure.doors || [])
      .filter(d => d.attachedToWall === wall.systemIdentifier);

    const children: TreeNode[] = [];

    // Add windows as children
    if (attachedWindows.length > 0) {
      children.push({
        id: `${wall.systemIdentifier}-windows`,
        label: `🪟 Windows on this wall (${attachedWindows.length})`,
        type: NodeType.CATEGORY,
        expanded: false,
        children: attachedWindows.map(w => this.createWindowNode(w))
      });
    }

    // Add doors as children
    if (attachedDoors.length > 0) {
      children.push({
        id: `${wall.systemIdentifier}-doors`,
        label: `🚪 Doors on this wall (${attachedDoors.length})`,
        type: NodeType.CATEGORY,
        expanded: false,
        children: attachedDoors.map(d => this.createDoorNode(d))
      });
    }

    return {
      id: wall.systemIdentifier,
      label: this.getWallLabel(wall),
      icon: '🧱',
      type: NodeType.COMPONENT,
      componentId: wall.systemIdentifier,
      expanded: false,
      children: children.length > 0 ? children : undefined,
      validationState: this.getValidationState(wall)
    };
  }

  private getWallLabel(wall: Wall): string {
    const orientation = this.guessOrientation(wall);
    const h2kLabel = wall.extensions?.h2kLabel;

    if (h2kLabel) {
      return `${wall.systemIdentifier} (${h2kLabel})`;
    }

    return `${wall.systemIdentifier} (${orientation})`;
  }

  private guessOrientation(wall: Wall): string {
    // Try to determine orientation from adjacent windows/doors
    // Or use cardinal direction if available
    // Fallback to generic label
    return "Wall";
  }
}
```

---

## 9. Component Templates

### 9.1 Template Library

```typescript
interface ComponentTemplate {
  id: string;
  name: string;
  description: string;
  type: ComponentType;
  category: string;
  data: Partial<HPXMLComponent>;
  icon?: string;
}

class TemplateLibrary {
  private templates: Map<ComponentType, ComponentTemplate[]>;

  getTemplatesForType(type: ComponentType): ComponentTemplate[] {
    return this.templates.get(type) || [];
  }

  createFromTemplate(
    templateId: string,
    customizations?: any
  ): HPXMLComponent {
    const template = this.findTemplate(templateId);
    return {
      ...template.data,
      ...customizations,
      systemIdentifier: this.generateId(template.type)
    };
  }
}

// Example templates
const windowTemplates: ComponentTemplate[] = [
  {
    id: "window-double-pane-low-e",
    name: "Double-pane, Low-E",
    description: "Standard energy-efficient window",
    type: ComponentType.WINDOW,
    category: "Standard",
    data: {
      type: "Window",
      properties: {
        uFactor: 0.28,
        shgc: 0.40,
        fractionOperable: 0
      }
    }
  },
  {
    id: "window-triple-pane",
    name: "Triple-pane",
    description: "High-performance window",
    type: ComponentType.WINDOW,
    category: "High Performance",
    data: {
      type: "Window",
      properties: {
        uFactor: 0.20,
        shgc: 0.35,
        fractionOperable: 0
      }
    }
  }
];
```

---

## 10. File Operations

### 10.1 File Handlers

```typescript
class FileHandler {
  async open(filePath: string): Promise<HPXMLDocument> {
    // Read file
    const xmlContent = await fs.readFile(filePath, 'utf-8');

    // Parse
    const parser = new HPXMLParser();
    const document = parser.parse(xmlContent);

    // Store file path
    document.filePath = filePath;

    // Add to recent files
    this.addToRecentFiles(filePath);

    return document;
  }

  async save(
    document: HPXMLDocument,
    filePath?: string
  ): Promise<void> {
    const targetPath = filePath || document.filePath;
    if (!targetPath) {
      throw new Error("No file path specified");
    }

    // Validate before saving
    const validation = await this.validate(document);
    if (validation.hasErrors) {
      const proceed = await this.confirmSaveWithErrors(validation);
      if (!proceed) return;
    }

    // Serialize
    const serializer = new HPXMLSerializer();
    const xmlContent = serializer.serialize(document);

    // Create backup
    if (await fs.exists(targetPath)) {
      await this.createBackup(targetPath);
    }

    // Write file
    await fs.writeFile(targetPath, xmlContent, 'utf-8');

    // Update document state
    document.filePath = targetPath;
    document.modified = false;
    document.lastSaved = new Date();
  }

  async autoSave(document: HPXMLDocument): Promise<void> {
    if (!document.modified || !document.filePath) return;

    const autoSavePath = this.getAutoSavePath(document.filePath);
    const serializer = new HPXMLSerializer();
    const xmlContent = serializer.serialize(document);

    await fs.writeFile(autoSavePath, xmlContent, 'utf-8');
  }

  private getAutoSavePath(filePath: string): string {
    const dir = path.dirname(filePath);
    const name = path.basename(filePath, '.xml');
    return path.join(dir, `.${name}.autosave.xml`);
  }
}
```

---

### 10.2 H2K Import Integration

The editor integrates with the existing H2K-HPXML converter to allow importing H2K files directly.

#### 10.2.1 Import Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                    Electron Main Process                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  H2K Import Service                                      │  │
│  │  ├─ Spawn Python subprocess                             │  │
│  │  │  └─ h2k-hpxml input.h2k --output temp.xml           │  │
│  │  │     --do-not-sim                                     │  │
│  │  ├─ Monitor stdout/stderr                               │  │
│  │  ├─ Parse progress updates                              │  │
│  │  └─ Handle completion/errors                            │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ↕                                     │
│                    IPC Communication                            │
│                           ↕                                     │
└────────────────────────────────────────────────────────────────┘
                            ↓
┌────────────────────────────────────────────────────────────────┐
│                   Renderer Process (UI)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Import Dialog                                           │  │
│  │  ├─ File picker (.h2k files)                            │  │
│  │  ├─ Conversion options                                  │  │
│  │  │  └─ Weather location, validation settings           │  │
│  │  └─ Progress indicator                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                           ↓                                     │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Post-Import Review                                      │  │
│  │  ├─ Show conversion warnings                            │  │
│  │  ├─ Preview HPXML structure                             │  │
│  │  └─ Confirm/Edit/Cancel options                         │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

#### 10.2.2 H2K Import Service (Main Process)

```typescript
// Main process (Node.js with full system access)
import { spawn } from 'child_process';
import { ipcMain } from 'electron';
import path from 'path';
import fs from 'fs/promises';

interface ImportOptions {
  h2kFilePath: string;
  outputPath?: string;
  weatherLocation?: string;
  skipSimulation: boolean;
  validateOutput: boolean;
}

interface ImportProgress {
  stage: 'parsing' | 'converting' | 'validating' | 'complete' | 'error';
  message: string;
  percentage: number;
}

interface ImportResult {
  success: boolean;
  hpxmlPath?: string;
  warnings: string[];
  errors: string[];
  conversionTime: number;
}

class H2KImportService {
  private pythonPath: string;
  private h2kHpxmlCommand: string;

  constructor() {
    // Auto-detect Python and h2k-hpxml command
    this.pythonPath = this.detectPythonPath();
    this.h2kHpxmlCommand = 'h2k-hpxml'; // Or full path if needed
  }

  async importH2KFile(
    options: ImportOptions,
    progressCallback: (progress: ImportProgress) => void
  ): Promise<ImportResult> {
    const startTime = Date.now();
    const warnings: string[] = [];
    const errors: string[] = [];

    try {
      // Generate temp output path if not specified
      const outputPath = options.outputPath ||
        await this.generateTempOutputPath(options.h2kFilePath);

      progressCallback({
        stage: 'parsing',
        message: 'Starting H2K file conversion...',
        percentage: 10
      });

      // Build command arguments
      const args = [
        options.h2kFilePath,
        '--output', outputPath
      ];

      if (options.skipSimulation) {
        args.push('--do-not-sim');
      }

      if (options.weatherLocation) {
        args.push('--weather', options.weatherLocation);
      }

      // Spawn h2k-hpxml process
      const result = await this.runConverter(args, progressCallback);

      // Check if output file was created
      const hpxmlExists = await this.fileExists(outputPath);
      if (!hpxmlExists) {
        throw new Error('Conversion completed but HPXML file was not created');
      }

      progressCallback({
        stage: 'validating',
        message: 'Validating generated HPXML...',
        percentage: 80
      });

      // Validate output if requested
      if (options.validateOutput) {
        const validationResult = await this.validateHPXML(outputPath);
        warnings.push(...validationResult.warnings);
        if (!validationResult.isValid) {
          errors.push(...validationResult.errors);
        }
      }

      progressCallback({
        stage: 'complete',
        message: 'Conversion complete!',
        percentage: 100
      });

      const conversionTime = Date.now() - startTime;

      return {
        success: true,
        hpxmlPath: outputPath,
        warnings,
        errors,
        conversionTime
      };

    } catch (error) {
      progressCallback({
        stage: 'error',
        message: error.message,
        percentage: 0
      });

      return {
        success: false,
        warnings,
        errors: [error.message, ...errors],
        conversionTime: Date.now() - startTime
      };
    }
  }

  private async runConverter(
    args: string[],
    progressCallback: (progress: ImportProgress) => void
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      const process = spawn(this.h2kHpxmlCommand, args, {
        stdio: ['ignore', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';

      process.stdout.on('data', (data) => {
        stdout += data.toString();

        // Parse progress from stdout
        const lines = data.toString().split('\n');
        for (const line of lines) {
          if (line.includes('Processing:')) {
            progressCallback({
              stage: 'converting',
              message: line.trim(),
              percentage: 40
            });
          } else if (line.includes('Writing HPXML')) {
            progressCallback({
              stage: 'converting',
              message: 'Generating HPXML output...',
              percentage: 70
            });
          }
        }
      });

      process.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      process.on('close', (code) => {
        if (code === 0) {
          resolve();
        } else {
          reject(new Error(
            `Conversion failed with exit code ${code}\n${stderr}`
          ));
        }
      });

      process.on('error', (err) => {
        reject(new Error(`Failed to start converter: ${err.message}`));
      });
    });
  }

  private async validateHPXML(hpxmlPath: string): Promise<{
    isValid: boolean;
    warnings: string[];
    errors: string[];
  }> {
    // Call Python validator
    return new Promise((resolve) => {
      const process = spawn('python', [
        '-m', 'h2k_hpxml.utils.hpxml_validator',
        hpxmlPath,
        '--verbose'
      ]);

      let output = '';
      process.stdout.on('data', (data) => { output += data.toString(); });
      process.stderr.on('data', (data) => { output += data.toString(); });

      process.on('close', (code) => {
        const isValid = code === 0;
        const warnings: string[] = [];
        const errors: string[] = [];

        // Parse validation output
        const lines = output.split('\n');
        for (const line of lines) {
          if (line.includes('Warning:')) {
            warnings.push(line.trim());
          } else if (line.includes('Error:') || line.includes('✗')) {
            errors.push(line.trim());
          }
        }

        resolve({ isValid, warnings, errors });
      });
    });
  }

  private async generateTempOutputPath(h2kPath: string): Promise<string> {
    const tempDir = await this.getTempDirectory();
    const basename = path.basename(h2kPath, '.h2k');
    const timestamp = Date.now();
    return path.join(tempDir, `${basename}_${timestamp}.xml`);
  }

  private async getTempDirectory(): Promise<string> {
    const tempDir = path.join(require('os').tmpdir(), 'h2k-hpxml-editor');
    await fs.mkdir(tempDir, { recursive: true });
    return tempDir;
  }

  private async fileExists(filePath: string): Promise<boolean> {
    try {
      await fs.access(filePath);
      return true;
    } catch {
      return false;
    }
  }

  private detectPythonPath(): string {
    // Try common Python installations
    // This is simplified - real implementation would be more robust
    const candidates = ['python3', 'python', 'py'];
    // Return first available or 'python' as default
    return 'python3';
  }
}

// Register IPC handlers
export function registerH2KImportHandlers(importService: H2KImportService) {
  ipcMain.handle('import-h2k', async (event, options: ImportOptions) => {
    return await importService.importH2KFile(options, (progress) => {
      // Send progress updates to renderer
      event.sender.send('import-progress', progress);
    });
  });
}
```

#### 10.2.3 Import Dialog UI Component (Renderer Process)

```typescript
// Renderer process (React component)
import React, { useState } from 'react';
import { Button, Dialog, DialogTitle, DialogContent,
         DialogActions, TextField, Checkbox, FormControlLabel,
         LinearProgress, Alert } from '@mui/material';

interface ImportDialogProps {
  open: boolean;
  onClose: () => void;
  onImportComplete: (hpxmlPath: string) => void;
}

export const H2KImportDialog: React.FC<ImportDialogProps> = ({
  open,
  onClose,
  onImportComplete
}) => {
  const [h2kFilePath, setH2kFilePath] = useState<string>('');
  const [skipSimulation, setSkipSimulation] = useState(true);
  const [validateOutput, setValidateOutput] = useState(true);
  const [importing, setImporting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [result, setResult] = useState<ImportResult | null>(null);

  const handleSelectFile = async () => {
    // Use Electron dialog to select .h2k file
    const result = await window.electron.dialog.showOpenDialog({
      title: 'Select H2K File',
      filters: [
        { name: 'H2K Files', extensions: ['h2k', 'H2K'] },
        { name: 'All Files', extensions: ['*'] }
      ],
      properties: ['openFile']
    });

    if (!result.canceled && result.filePaths.length > 0) {
      setH2kFilePath(result.filePaths[0]);
    }
  };

  const handleImport = async () => {
    if (!h2kFilePath) return;

    setImporting(true);
    setProgress(0);
    setProgressMessage('Initializing...');
    setResult(null);

    // Listen for progress updates
    const removeListener = window.electron.ipcRenderer.on(
      'import-progress',
      (progress: ImportProgress) => {
        setProgress(progress.percentage);
        setProgressMessage(progress.message);
      }
    );

    try {
      const importResult = await window.electron.ipcRenderer.invoke(
        'import-h2k',
        {
          h2kFilePath,
          skipSimulation,
          validateOutput
        }
      );

      setResult(importResult);

      if (importResult.success) {
        // Show success for a moment, then load the file
        setTimeout(() => {
          onImportComplete(importResult.hpxmlPath);
          onClose();
        }, 1500);
      }

    } catch (error) {
      setResult({
        success: false,
        warnings: [],
        errors: [error.message],
        conversionTime: 0
      });
    } finally {
      setImporting(false);
      removeListener();
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Import H2K File</DialogTitle>

      <DialogContent>
        {/* File Selection */}
        <div style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
          <TextField
            fullWidth
            label="H2K File"
            value={h2kFilePath}
            disabled
            placeholder="Select a .h2k file..."
          />
          <Button
            variant="contained"
            onClick={handleSelectFile}
            disabled={importing}
          >
            Browse...
          </Button>
        </div>

        {/* Options */}
        <FormControlLabel
          control={
            <Checkbox
              checked={skipSimulation}
              onChange={(e) => setSkipSimulation(e.target.checked)}
              disabled={importing}
            />
          }
          label="Skip EnergyPlus simulation (faster)"
        />

        <FormControlLabel
          control={
            <Checkbox
              checked={validateOutput}
              onChange={(e) => setValidateOutput(e.target.checked)}
              disabled={importing}
            />
          }
          label="Validate HPXML output"
        />

        {/* Progress */}
        {importing && (
          <div style={{ marginTop: '16px' }}>
            <LinearProgress variant="determinate" value={progress} />
            <p style={{ marginTop: '8px', fontSize: '14px', color: '#666' }}>
              {progressMessage}
            </p>
          </div>
        )}

        {/* Results */}
        {result && !importing && (
          <div style={{ marginTop: '16px' }}>
            {result.success ? (
              <>
                <Alert severity="success">
                  Conversion completed in {(result.conversionTime / 1000).toFixed(1)}s
                </Alert>

                {result.warnings.length > 0 && (
                  <Alert severity="warning" style={{ marginTop: '8px' }}>
                    <strong>Warnings ({result.warnings.length}):</strong>
                    <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
                      {result.warnings.slice(0, 5).map((warning, i) => (
                        <li key={i}>{warning}</li>
                      ))}
                      {result.warnings.length > 5 && (
                        <li>...and {result.warnings.length - 5} more</li>
                      )}
                    </ul>
                  </Alert>
                )}
              </>
            ) : (
              <Alert severity="error">
                <strong>Conversion Failed</strong>
                <ul style={{ margin: '8px 0 0 0', paddingLeft: '20px' }}>
                  {result.errors.map((error, i) => (
                    <li key={i}>{error}</li>
                  ))}
                </ul>
              </Alert>
            )}
          </div>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose} disabled={importing}>
          Cancel
        </Button>
        <Button
          onClick={handleImport}
          variant="contained"
          disabled={!h2kFilePath || importing}
        >
          {importing ? 'Converting...' : 'Import'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
```

#### 10.2.4 Batch Import Support

For importing multiple H2K files:

```typescript
interface BatchImportOptions {
  h2kFiles: string[];
  outputDirectory: string;
  skipSimulation: boolean;
  validateOutput: boolean;
  parallelCount: number; // Number of concurrent conversions
}

interface BatchImportProgress {
  total: number;
  completed: number;
  failed: number;
  currentFile: string;
  results: ImportResult[];
}

class BatchH2KImportService {
  async importBatch(
    options: BatchImportOptions,
    progressCallback: (progress: BatchImportProgress) => void
  ): Promise<BatchImportProgress> {
    const results: ImportResult[] = [];
    let completed = 0;
    let failed = 0;

    // Process files in parallel (limited concurrency)
    const queue = [...options.h2kFiles];
    const active: Promise<void>[] = [];

    while (queue.length > 0 || active.length > 0) {
      // Start new conversions up to parallelCount
      while (active.length < options.parallelCount && queue.length > 0) {
        const h2kFile = queue.shift()!;

        const promise = this.importSingleFile({
          h2kFilePath: h2kFile,
          outputPath: this.getOutputPath(h2kFile, options.outputDirectory),
          skipSimulation: options.skipSimulation,
          validateOutput: options.validateOutput
        }).then(result => {
          results.push(result);
          if (result.success) {
            completed++;
          } else {
            failed++;
          }

          progressCallback({
            total: options.h2kFiles.length,
            completed,
            failed,
            currentFile: h2kFile,
            results: [...results]
          });
        });

        active.push(promise);
      }

      // Wait for one to complete
      if (active.length > 0) {
        await Promise.race(active);
        // Remove completed promises
        const stillActive = active.filter(p => {
          const status = (p as any)._status;
          return status !== 'fulfilled' && status !== 'rejected';
        });
        active.length = 0;
        active.push(...stillActive);
      }
    }

    return {
      total: options.h2kFiles.length,
      completed,
      failed,
      currentFile: '',
      results
    };
  }

  private async importSingleFile(options: ImportOptions): Promise<ImportResult> {
    const importService = new H2KImportService();
    return await importService.importH2KFile(options, () => {});
  }

  private getOutputPath(h2kPath: string, outputDir: string): string {
    const basename = path.basename(h2kPath, '.h2k');
    return path.join(outputDir, `${basename}.xml`);
  }
}
```

#### 10.2.5 Integration with File Menu

```typescript
// Add to main menu
const menuTemplate = [
  {
    label: 'File',
    submenu: [
      {
        label: 'New HPXML...',
        accelerator: 'CmdOrCtrl+N',
        click: () => { /* ... */ }
      },
      {
        label: 'Open HPXML...',
        accelerator: 'CmdOrCtrl+O',
        click: () => { /* ... */ }
      },
      { type: 'separator' },
      {
        label: 'Import from H2K...',
        accelerator: 'CmdOrCtrl+Shift+I',
        click: () => {
          mainWindow.webContents.send('show-h2k-import-dialog');
        }
      },
      {
        label: 'Batch Import H2K Files...',
        click: () => {
          mainWindow.webContents.send('show-batch-import-dialog');
        }
      },
      { type: 'separator' },
      {
        label: 'Save',
        accelerator: 'CmdOrCtrl+S',
        click: () => { /* ... */ }
      },
      // ... rest of menu
    ]
  }
];
```

#### 10.2.6 Error Handling & User Feedback

Common error scenarios and handling:

1. **Python/h2k-hpxml not found**
   - Show setup dialog with instructions
   - Link to installation documentation
   - Allow manual path configuration

2. **Invalid H2K file**
   - Show specific validation errors from converter
   - Suggest fixes if possible

3. **Conversion warnings**
   - Display in post-import review dialog
   - Allow user to accept or cancel
   - Log warnings to help documentation

4. **HPXML validation failures**
   - Show which elements failed validation
   - Offer to open anyway (for advanced users)
   - Provide links to relevant documentation

#### 10.2.7 Configuration Storage

Store import preferences:

```typescript
interface ImportPreferences {
  lastImportDirectory: string;
  defaultSkipSimulation: boolean;
  defaultValidateOutput: boolean;
  batchParallelCount: number;
  pythonPath?: string;
  h2kHpxmlPath?: string;
}

// Store in electron-store or similar
const importPreferences = new Store<ImportPreferences>({
  name: 'import-preferences',
  defaults: {
    lastImportDirectory: '',
    defaultSkipSimulation: true,
    defaultValidateOutput: true,
    batchParallelCount: 4
  }
});
```

---

## 11. Undo/Redo System

### 11.1 Command Pattern

```typescript
interface Command {
  execute(): void;
  undo(): void;
  redo(): void;
  canUndo(): boolean;
  canRedo(): boolean;
}

class UpdateComponentCommand implements Command {
  constructor(
    private componentId: string,
    private oldData: any,
    private newData: any,
    private store: Store
  ) {}

  execute(): void {
    this.store.dispatch(
      updateComponent(this.componentId, this.newData)
    );
  }

  undo(): void {
    this.store.dispatch(
      updateComponent(this.componentId, this.oldData)
    );
  }

  redo(): void {
    this.execute();
  }

  canUndo(): boolean {
    return true;
  }

  canRedo(): boolean {
    return true;
  }
}

class CommandHistory {
  private past: Command[] = [];
  private future: Command[] = [];
  private maxSize = 50;

  execute(command: Command): void {
    command.execute();
    this.past.push(command);
    this.future = []; // Clear redo stack

    if (this.past.length > this.maxSize) {
      this.past.shift();
    }
  }

  undo(): void {
    const command = this.past.pop();
    if (command && command.canUndo()) {
      command.undo();
      this.future.push(command);
    }
  }

  redo(): void {
    const command = this.future.pop();
    if (command && command.canRedo()) {
      command.redo();
      this.past.push(command);
    }
  }

  canUndo(): boolean {
    return this.past.length > 0;
  }

  canRedo(): boolean {
    return this.future.length > 0;
  }

  clear(): void {
    this.past = [];
    this.future = [];
  }
}
```

---

## 12. Testing Strategy

### 12.1 Unit Tests

```typescript
// Component tests
describe('TreeBuilder', () => {
  it('should build wall nodes with attached windows', () => {
    const enclosure = createMockEnclosure();
    const tree = treeBuilder.buildComponentTree(enclosure);
    const wallNode = findNodeById(tree, 'Wall1');

    expect(wallNode.children).toHaveLength(1);
    expect(wallNode.children[0].label).toContain('Windows');
  });

  it('should validate wall references', () => {
    const wall = createMockWall();
    const validation = validator.validateComponent(wall);

    expect(validation.isValid).toBe(true);
  });
});

// Parser tests
describe('HPXMLParser', () => {
  it('should parse valid HPXML v4.0 document', () => {
    const xml = fs.readFileSync('test-fixtures/valid.xml', 'utf-8');
    const doc = parser.parse(xml);

    expect(doc.schemaVersion).toBe('4.0');
    expect(doc.buildings).toHaveLength(1);
  });

  it('should handle missing optional elements', () => {
    const xml = fs.readFileSync('test-fixtures/minimal.xml', 'utf-8');
    const doc = parser.parse(xml);

    expect(doc.buildings[0].enclosure.skylights).toBeUndefined();
  });
});
```

### 12.2 Integration Tests

```typescript
// End-to-end workflow tests
describe('Editor Workflow', () => {
  it('should load, edit, and save document', async () => {
    // Load
    const doc = await fileHandler.open('test.xml');

    // Edit
    const wall = findComponent(doc, 'Wall1');
    wall.properties.area = 350;

    // Save
    await fileHandler.save(doc);

    // Reload and verify
    const reloaded = await fileHandler.open('test.xml');
    const reloadedWall = findComponent(reloaded, 'Wall1');
    expect(reloadedWall.properties.area).toBe(350);
  });

  it('should maintain references when duplicating', () => {
    const wall = createWallWithWindows();
    const duplicate = duplicateComponent(wall);

    expect(duplicate.systemIdentifier).not.toBe(wall.systemIdentifier);
    // Windows should reference new wall
    const window = findAttachedWindow(duplicate);
    expect(window.attachedToWall).toBe(duplicate.systemIdentifier);
  });
});
```

### 12.3 UI Tests

```typescript
// React Testing Library
describe('PropertiesPanel', () => {
  it('should display wall properties', () => {
    const wall = createMockWall();
    render(<PropertiesPanel component={wall} />);

    expect(screen.getByLabelText('Area')).toHaveValue(320);
    expect(screen.getByLabelText('R-Value')).toHaveValue(20);
  });

  it('should call onChange when field is edited', () => {
    const onChange = jest.fn();
    const wall = createMockWall();
    render(<PropertiesPanel component={wall} onChange={onChange} />);

    const areaField = screen.getByLabelText('Area');
    fireEvent.change(areaField, { target: { value: '350' } });

    expect(onChange).toHaveBeenCalledWith({
      area: 350
    });
  });

  it('should show validation errors', () => {
    const wall = createMockWall({ area: -1 });
    render(<PropertiesPanel component={wall} />);

    expect(screen.getByText(/must be greater than 0/i)).toBeInTheDocument();
  });
});
```

---

## 13. Performance Optimization

### 13.1 Strategies

```typescript
// 1. Virtual scrolling for large trees
import { FixedSizeTree } from 'react-vtree';

// 2. Memoization for expensive calculations
const calculatedRValue = useMemo(
  () => calculateAssemblyRValue(wall),
  [wall.insulation, wall.thickness]
);

// 3. Debounced validation
const debouncedValidate = useMemo(
  () => debounce(validateComponent, 300),
  []
);

// 4. Lazy loading of component forms
const WallForm = lazy(() => import('./forms/WallForm'));

// 5. Web Workers for XML parsing
const parserWorker = new Worker('hpxml-parser.worker.js');
```

### 13.2 Data Optimization

```typescript
// Immutable updates with Immer
import produce from 'immer';

const updateWall = produce((draft: HPXMLDocument, wallId: string, updates: any) => {
  const wall = findWallById(draft, wallId);
  Object.assign(wall.properties, updates);
});

// Indexed access for fast lookups
interface DocumentIndex {
  componentsById: Map<string, HPXMLComponent>;
  componentsByType: Map<ComponentType, HPXMLComponent[]>;
  referenceIndex: Map<string, Set<string>>;  // targetId -> referrer IDs
}
```

---

## 14. Deployment

### 14.1 Build Configuration

```yaml
# electron-builder.yml
appId: com.h2khpxml.editor
productName: H2K-HPXML Building Editor
directories:
  output: dist
files:
  - "build/**/*"
  - "node_modules/**/*"
  - "python/**/*"
  - "package.json"
extraResources:
  - "resources/**/*"
  - "src/h2k_hpxml/resources/schemas/**/*"
win:
  target: nsis
  icon: build/icon.ico
mac:
  target: dmg
  icon: build/icon.icns
linux:
  target: AppImage
  icon: build/icon.png
```

### 14.2 Auto-Update

```typescript
// Electron auto-updater
import { autoUpdater } from 'electron-updater';

autoUpdater.checkForUpdatesAndNotify();

autoUpdater.on('update-available', () => {
  dialog.showMessageBox({
    type: 'info',
    title: 'Update Available',
    message: 'A new version is available. Download now?',
    buttons: ['Yes', 'No']
  }).then(result => {
    if (result.response === 0) {
      autoUpdater.downloadUpdate();
    }
  });
});
```

---

## 15. User Documentation

### 15.1 Help System

```typescript
// Context-sensitive help
interface HelpContent {
  componentType: ComponentType;
  field?: string;
  title: string;
  content: string;
  examples?: string[];
  relatedTopics?: string[];
}

// Help tooltip component
const HelpTooltip: React.FC<{ topic: string }> = ({ topic }) => {
  const content = useHelpContent(topic);

  return (
    <Tooltip title={content.title} content={content.content}>
      <HelpIcon />
    </Tooltip>
  );
};
```

### 15.2 Documentation Structure

```
docs/
├── user-guide/
│   ├── getting-started.md
│   ├── interface-overview.md
│   ├── working-with-walls.md
│   ├── working-with-windows.md
│   ├── hvac-systems.md
│   └── validation.md
│
├── tutorials/
│   ├── create-new-building.md
│   ├── import-from-h2k.md
│   └── common-workflows.md
│
└── reference/
    ├── component-reference.md
    ├── validation-rules.md
    └── keyboard-shortcuts.md
```

---

## 16. Development Phases

### Phase 1: Foundation (2-3 weeks)
- Set up project structure
- Implement HPXML parser/serializer
- Create basic data model
- Set up state management

**Deliverables:**
- Project scaffolding complete
- HPXML can be loaded and saved
- Basic Redux store configured

### Phase 2: Core UI (3-4 weeks)
- Build tree navigator component
- Build properties panel framework
- Implement basic forms (walls, windows)
- Add file open/save
- Implement H2K import integration

**Deliverables:**
- Two-pane layout functional
- Can view HPXML in tree
- Can edit wall/window properties
- File operations working
- H2K files can be imported via subprocess
- Import dialog with progress tracking

### Phase 3: Component Forms (3-4 weeks)
- Implement all component-specific forms
- Add validation layer
- Implement templates
- Add undo/redo

**Deliverables:**
- All HPXML components editable
- Validation showing inline
- Template library functional
- Undo/redo working

### Phase 4: Advanced Features (2-3 weeks)
- Add search/filter
- Implement bulk operations
- Add comparison view
- Integrate Python validator
- Add batch H2K import functionality

**Deliverables:**
- Search/filter working
- Bulk edit functional
- Python validator integrated
- Comparison view complete
- Batch H2K import with parallel processing

### Phase 5: Polish & Testing (2-3 weeks)
- UI/UX refinement
- Performance optimization
- Comprehensive testing
- Bug fixes

**Deliverables:**
- UI polished and consistent
- Performance targets met
- Test coverage > 80%
- Critical bugs fixed

### Phase 6: Documentation & Deployment (1-2 weeks)
- User documentation
- Build scripts
- Installer
- Auto-update setup

**Deliverables:**
- User guide complete
- Installers for all platforms
- Auto-update working
- Release notes

**Total Estimated Time: 13-19 weeks (3-5 months)**

---

## 17. Success Metrics

### Performance Metrics
- Load 5000-component HPXML file in < 2 seconds
- Update component and see validation in < 100ms
- Tree render with 1000+ nodes in < 500ms
- Auto-save operation in < 200ms
- H2K import conversion completes in < 10 seconds (typical file)
- Batch import processes 4+ files in parallel efficiently

### Reliability Metrics
- Zero data loss on crashes (auto-save)
- 95%+ of validation rules match Python validator
- < 1% false positives in validation
- Undo/redo works for 100% of operations

### Usability Metrics
- User can create basic building in < 5 minutes
- User can import H2K file in < 3 clicks
- 90%+ of operations require ≤ 3 clicks
- Average task completion time < baseline
- User satisfaction score > 4/5
- H2K import success rate > 95%

### Quality Metrics
- Test coverage > 80%
- Zero critical bugs at release
- < 5 high-priority bugs at release
- Performance targets met

---

## Appendix A: UI Mockups Reference

### Tree Navigator
```
┌─────────────────────────────────────┐
│ 🔍 Search components...             │
├─────────────────────────────────────┤
│ [+] Add   [-] Delete   [↕️] Move    │
├─────────────────────────────────────┤
│ ▼ 🏠 Building: MyBuilding           │
│   ├─▼ 🧱 Above-Grade Walls (4)      │
│   │  ├─▼ Wall1 (North) *            │
│   │  │  ├─ 🪟 Window1 (15 sq ft)    │
│   │  │  ├─ 🪟 Window2 (6 sq ft)     │
│   │  │  └─ 🚪 Door1 (20 sq ft)      │
│   │  ├─▶ Wall2 (South)              │
│   │  ├─▶ Wall3 (East)               │
│   │  └─▶ Wall4 (West)               │
└─────────────────────────────────────┘
```

### Properties Panel
```
┌───────────────────────────────────────┐
│ 🧱 Wall Properties: Wall1    [✓] [X] │
├───────────────────────────────────────┤
│ [General] [Insulation] [Attachments] │
├───────────────────────────────────────┤
│ Area:  [320.0    ] sq ft              │
│ R-Val: [20.0     ] hr·ft²·°F/Btu     │
│                                       │
│ Exterior: [Outside ▼]                 │
│ Interior: [Conditioned space ▼]       │
└───────────────────────────────────────┘
```

---

## Appendix B: Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Open File | Ctrl+O |
| Import H2K File | Ctrl+Shift+I |
| Save | Ctrl+S |
| Save As | Ctrl+Shift+S |
| New Component | Ctrl+N |
| Duplicate | Ctrl+D |
| Delete | Delete |
| Undo | Ctrl+Z |
| Redo | Ctrl+Y |
| Find | Ctrl+F |
| Validate | F5 |
| Toggle Tree | F9 |

---

## Appendix C: Related Documents

- **HPXML Subset Schema**: `src/h2k_hpxml/resources/schemas/hpxml_subset.xsd`
- **HPXML Subset Documentation**: `docs/HPXML_SUBSET.md`
- **Python Validator**: `src/h2k_hpxml/utils/hpxml_validator.py`
- **User Guide**: `docs/USER_GUIDE.md`
- **Project README**: `README.md`

---

## Document Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Jan 2025 | H2K-HPXML Team | Initial specification |
| 1.1 | Jan 2025 | H2K-HPXML Team | Added H2K import integration (Section 10.2) |

---

**End of Document**
