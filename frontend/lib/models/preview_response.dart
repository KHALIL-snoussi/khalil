/// Models for API communication
class CropRect {
  final int x;
  final int y;
  final int w;
  final int h;

  CropRect({
    required this.x,
    required this.y,
    required this.w,
    required this.h,
  });

  Map<String, dynamic> toJson() => {
        'x': x,
        'y': y,
        'w': w,
        'h': h,
      };

  factory CropRect.fromJson(Map<String, dynamic> json) => CropRect(
        x: json['x'],
        y: json['y'],
        w: json['w'],
        h: json['h'],
      );
}

class GridSize {
  final int w;
  final int h;

  GridSize({this.w = 100, this.h = 140});

  Map<String, dynamic> toJson() => {'w': w, 'h': h};

  factory GridSize.fromJson(Map<String, dynamic> json) => GridSize(
        w: json['w'] ?? 100,
        h: json['h'] ?? 140,
      );
}

class ProcessingOptions {
  final double gamma;
  final double edgeBoost;
  final String dither;
  final double ditherStrength;
  final bool autoFaceCrop;
  final double backgroundDesat;
  final bool speckleCleanup;

  ProcessingOptions({
    this.gamma = 1.0,
    this.edgeBoost = 0.25,
    this.dither = 'fs',
    this.ditherStrength = 1.0,
    this.autoFaceCrop = false,
    this.backgroundDesat = 0.0,
    this.speckleCleanup = false,
  });

  Map<String, dynamic> toJson() => {
        'gamma': gamma,
        'edge_boost': edgeBoost,
        'dither': dither,
        'dither_strength': ditherStrength,
        'auto_face_crop': autoFaceCrop,
        'background_desat': backgroundDesat,
        'speckle_cleanup': speckleCleanup,
      };
}

class PreviewPayload {
  final CropRect crop;
  final int rotateDeg;
  final GridSize grid;
  final List<String> styles;
  final ProcessingOptions options;

  PreviewPayload({
    required this.crop,
    this.rotateDeg = 0,
    GridSize? grid,
    List<String>? styles,
    ProcessingOptions? options,
  })  : grid = grid ?? GridSize(),
        styles = styles ?? ['original', 'vintage', 'popart'],
        options = options ?? ProcessingOptions();

  Map<String, dynamic> toJson() => {
        'crop': crop.toJson(),
        'rotate_deg': rotateDeg,
        'grid': grid.toJson(),
        'styles': styles,
        'options': options.toJson(),
      };
}

class PreviewResponse {
  final String jobId;
  final GridSize grid;
  final Map<String, String> previews;
  final Map<String, List<int>> counts;

  PreviewResponse({
    required this.jobId,
    required this.grid,
    required this.previews,
    required this.counts,
  });

  factory PreviewResponse.fromJson(Map<String, dynamic> json) {
    return PreviewResponse(
      jobId: json['job_id'],
      grid: GridSize.fromJson(json['grid']),
      previews: Map<String, String>.from(json['previews']),
      counts: (json['counts'] as Map<String, dynamic>).map(
        (key, value) => MapEntry(key, List<int>.from(value)),
      ),
    );
  }
}

class FinalRequest {
  final String jobId;
  final String style;
  final GridSize grid;
  final String paletteId;
  final CropRect crop;
  final int rotateDeg;
  final ProcessingOptions options;

  FinalRequest({
    required this.jobId,
    required this.style,
    required this.grid,
    required this.paletteId,
    required this.crop,
    this.rotateDeg = 0,
    ProcessingOptions? options,
  }) : options = options ?? ProcessingOptions();

  Map<String, dynamic> toJson() => {
        'job_id': jobId,
        'style': style,
        'grid': grid.toJson(),
        'palette_id': paletteId,
        'crop': crop.toJson(),
        'rotate_deg': rotateDeg,
        'options': options.toJson(),
      };
}
