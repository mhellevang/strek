// Paper jig for P2S plotting (UMTS) — an L-bracket that self-registers
// against the plate's back and right edges and places the sheet at the
// alignment margins (29 mm from the right, 41 mm from the back, see
// README "Paper position is critical").
//
// Use: place the jig on the plate (lips over the back/right edges),
// slide the sheet in under the flanges until it butts against the inner
// edges, tape the two free corners. The jig CAN stay on during plotting
// (1 mm base, the pen has a 3 mm Z hop and a 5 mm drawing margin).
//
// Marks (slots through the base):
//   - back arm: the sheet's LEFT edge (x=17)
//   - right arm, solid slot: A5 landscape front edge (148 mm sheet)
//   - right arm, dashed slot: 210×200 front edge (cut A4)
//
// The STL is exported in PRINT ORIENTATION (lips up, flanges toward the
// plate) — print as-is, no supports. Flip it over for use.
//
// Coordinates here: bed coordinates, (0,0) = the build area's front-left
// corner, X toward the right, Y toward the back wall. Z=0 = plate surface.

/* ---------- MEASURE THESE ON THE MACHINE BEFORE THE FIRST PRINT ---------- */
edge_to_bed = 1.0;  // plate edge beyond the build area, per side (ESTIMATE)
lip_drop    = 1.2;  // how far the lip hangs down along the plate edge —
                    // too long and it hits the heatbed and lifts the jig
lip_clear   = 0.3;  // clearance lip <-> plate edge
// Notches in the back lip for the plate's locating pins: [center-X, ...] (ESTIMATE)
pin_notches = [45, 211];
notch_w     = 18;
/* -------------------------------------------------------------------------- */

bed = 256;
paper_right_margin = 29;            // sheet's right edge from the build area's right edge
paper_back_margin  = 41;            // sheet's back edge from the build area's back edge
paper_x = bed - paper_right_margin; // 227 — sheet right edge (fence line)
paper_y = bed - paper_back_margin;  // 215 — sheet back edge (fence line)

t           = 1.0;  // base thickness — keep <= 1.2 (pen travel clearance is 3 mm)
flange_over = 3;    // flange reach over the sheet (holds the edge down)
flange_gap  = 0.4;  // air under the flange (sheet is ~0.1)
lip_t       = 2.0;  // lip thickness

paper_left_mark = 17;  // the sheet's left edge (227 - 210)
a5_front_mark   = paper_y - 148;  // 67 — A5 landscape front edge
cut_front_mark  = paper_y - 200;  // 15 — 210x200 front edge

arm_left  = paper_left_mark - 3;  // the back arm covers the left mark
arm_front = cut_front_mark - 3;   // the right arm covers the 200 mark

plate_x = bed + edge_to_bed;            // the plate's physical right edge
plate_y = bed + edge_to_bed;            // the plate's physical back edge
outer_x = plate_x + lip_clear + lip_t;
outer_y = plate_y + lip_clear + lip_t;

module base() {
    // L shape: back arm + right arm, inner edges = the fence lines
    translate([arm_left, paper_y, 0])
        cube([outer_x - arm_left, outer_y - paper_y, t]);
    translate([paper_x, arm_front, 0])
        cube([outer_x - paper_x, outer_y - arm_front, t]);
}

module flanges() {
    // hover flange_gap above the plate, reach flange_over in over the sheet
    translate([paper_left_mark, paper_y - flange_over, flange_gap])
        cube([paper_x - paper_left_mark, flange_over, t - flange_gap]);
    translate([paper_x - flange_over, arm_front + 3, flange_gap])
        cube([flange_over, paper_y - arm_front - 3, t - flange_gap]);
}

module lips() {
    translate([plate_x + lip_clear, arm_front, -lip_drop])
        cube([lip_t, outer_y - arm_front, lip_drop + t]);
    translate([arm_left, plate_y + lip_clear, -lip_drop])
        cube([outer_x - arm_left, lip_t, lip_drop + t]);
}

module slot(x0, x1, y0, y1) {
    translate([x0, y0, -lip_drop - 1])
        cube([x1 - x0, y1 - y0, lip_drop + t + 2]);
}

module cutouts() {
    // pin notches — cut through the lip AND the base at the back edge
    for (cx = pin_notches)
        translate([cx - notch_w / 2, plate_y - 1, -lip_drop - 1])
            cube([notch_w, outer_y - plate_y + 2, lip_drop + t + 2]);

    // mark slots (0.8 mm wide, through the base)
    // the sheet's left edge
    slot(paper_left_mark - 0.4, paper_left_mark + 0.4, paper_y + 3, paper_y + 15);
    // A5 front edge (solid)
    slot(paper_x + 5, paper_x + 17, a5_front_mark - 0.4, a5_front_mark + 0.4);
    // 210x200 front edge (dashed)
    slot(paper_x + 5,  paper_x + 10, cut_front_mark - 0.4, cut_front_mark + 0.4);
    slot(paper_x + 12, paper_x + 17, cut_front_mark - 0.4, cut_front_mark + 0.4);
}

module jig() {
    difference() {
        union() { base(); flanges(); lips(); }
        cutouts();
    }
}

// Export in print orientation: rotated 180° about X (a true flip, not a
// mirror), raised so the lowest point sits at z=0.
rotate([180, 0, 0]) translate([0, 0, -t]) jig();
