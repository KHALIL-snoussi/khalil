# Diamond Painting Generator - Frontend

Flutter web application for generating diamond painting patterns.

## Setup

### Prerequisites

- Flutter 3.x or higher
- Web browser (Chrome recommended)

### Installation

```bash
cd frontend
flutter pub get
```

## Running

### Development Mode

```bash
flutter run -d chrome
```

### Build for Production

```bash
flutter build web
```

The built files will be in `build/web/`.

## Features

- **Upload Screen**: Select and upload photos (up to 15 MB)
- **Crop Screen**: Crop and rotate images to portrait aspect ratio
- **Preview Screen**: View three style previews (Original, Vintage, Pop Art)
- **Download Screen**: Download final pattern pack as ZIP

## Configuration

Edit `lib/services/api.dart` to change the backend URL:

```dart
ApiService({this.baseUrl = 'http://localhost:8000'});
```

## Project Structure

```
lib/
  main.dart              # App entry point
  models/
    preview_response.dart  # Data models
  services/
    api.dart            # API client
  screens/
    upload_screen.dart   # Photo upload
    crop_screen.dart     # Crop/rotate
    preview_screen.dart  # Style previews
    download_screen.dart # Final download
```
