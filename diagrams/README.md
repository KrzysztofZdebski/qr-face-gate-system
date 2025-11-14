# UML Diagrams

This folder contains all UML diagrams for the QR Face Gate System, separated into individual files.

## Diagram Files

1. **01_class_diagram.puml** - Class diagram showing the main classes and their relationships
2. **02_sequence_user_registration.puml** - Sequence diagram for user registration flow
3. **03_sequence_verification.puml** - Sequence diagram for access verification flow
4. **04_component_diagram.puml** - Component diagram showing system architecture
5. **05_use_case_diagram.puml** - Use case diagram showing user interactions
6. **06_activity_registration_flow.puml** - Activity diagram for registration process
7. **07_activity_verification_flow.puml** - Activity diagram for verification process
8. **08_deployment_diagram.puml** - Deployment diagram showing system deployment

## How to View

### Option 1: Online Viewer
1. Open any `.puml` file
2. Copy its content
3. Go to http://www.plantuml.com/plantuml/uml/
4. Paste and view

### Option 2: VS Code
1. Install the "PlantUML" extension
2. Open any `.puml` file
3. Press `Alt+D` to preview

### Option 3: Command Line
```bash
# Install PlantUML (Fedora)
sudo dnf install plantuml

# Generate all diagrams as PNG
cd diagrams
for file in *.puml; do
    plantuml "$file"
done
```

### Option 4: Generate All at Once
```bash
# From project root
plantuml diagrams/*.puml
```

## Diagram Descriptions

### Class Diagram
Shows the core classes:
- `User`: Database model
- `FlaskApp`: Main application
- `QRCodeGenerator`: QR code service
- `FaceRecognitionService`: Face processing
- `DatabaseService`: Database operations

### Sequence Diagrams
Show interactions over time:
- **User Registration**: Complete registration flow
- **Verification**: Complete verification flow

### Component Diagram
Shows layered architecture:
- Frontend, Application, Service, Data layers
- External libraries and dependencies

### Use Case Diagram
Shows all user interactions with the system

### Activity Diagrams
Show decision flows:
- Registration process with error handling
- Verification process with matching logic

### Deployment Diagram
Shows physical deployment:
- Client machine (Browser, Camera)
- Server machine (Flask, Database, Files)
- Python environment (Libraries)

