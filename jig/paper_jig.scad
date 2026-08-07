// Paper jig for P2S plotting — a window frame that surrounds the sheet
// on all four sides and registers against the plate's back and right
// edges. The window places the sheet at the alignment margins (29 mm
// from the right, 41 mm from the back, see README "Paper position is
// critical").
//
// Use: OFF the machine, drop the sheet into the window (a shallow
// pocket — the sheet lies flush on the table/plate inside it) and tape
// its corners to the frame top. Carry the frame to the printer and
// hook the lips over the plate's back/right edges. The jig stays on
// during plotting (1 mm base, the pen has a 3 mm Z hop and a 5 mm
// drawing margin).
//
// The STL is exported in PRINT ORIENTATION (lips up) — print as-is,
// no supports. Flip it over for use.
//
// Coordinates here: bed coordinates, (0,0) = the build area's front-left
// corner, X toward the right, Y toward the back wall. Z=0 = plate surface.

/* ---------- MEASURE THESE ON THE MACHINE BEFORE THE FIRST PRINT ---------- */
edge_to_bed = 1.0;  // plate edge beyond the build area, per side (ESTIMATE)
lip_drop    = 1.2;  // how far the lip hangs down along the plate edge —
                    // too long and it hits the heatbed and lifts the jig
lip_clear   = 0.3;  // clearance lip <-> plate edge
// The back lip stops here: the plate's rear handle tab starts at x~92
// (from Bambu Studio's bbl-3dp-X1.stl), and to its right the machine
// has a further obstruction not present in any STL — so everything
// from the tab to the right edge is cut away (lip + base overhang).
// Registration still works: back lip left of here locks Y + rotation,
// the right lip locks X.
back_lip_end = 88;
/* ---------- PAPER FORMAT (one frame per format) --------------------------- */
paper_w   = 210;  // A5 landscape 210x148; cut A4 = 210x200
paper_h   = 148;
win_clear = 0.3;  // window <-> sheet clearance, per side
/* -------------------------------------------------------------------------- */

bed = 256;
paper_right_margin = 29;            // sheet's right edge from the build area's right edge
paper_back_margin  = 41;            // sheet's back edge from the build area's back edge
paper_x = bed - paper_right_margin; // 227 — sheet right edge
paper_y = bed - paper_back_margin;  // 215 — sheet back edge
sheet_left  = paper_x - paper_w;    // 17
sheet_front = paper_y - paper_h;    // 67 (A5)

t     = 1.0;  // base thickness — keep <= 1.2 (pen travel clearance is 3 mm)
lip_t = 2.0;  // lip thickness

border_left  = 13;  // frame border = tape landing area
border_front = 15;

plate_x = bed + edge_to_bed;         // the plate's physical right edge
plate_y = bed + edge_to_bed;         // the plate's physical back edge
outer_x = plate_x + lip_clear + lip_t;
outer_y = plate_y + lip_clear + lip_t;
frame_left  = sheet_left - border_left;
frame_front = sheet_front - border_front;

// the frame itself must fit on the 256 mm bed to be printable
assert(outer_x - frame_left <= bed, "frame too wide — shrink border_left");
assert(outer_y - frame_front <= bed, "frame too deep — shrink border_front");

module base() {
    difference() {
        translate([frame_left, frame_front, 0])
            cube([outer_x - frame_left, outer_y - frame_front, t]);
        // the window (shallow pocket — sheet lies on the plate inside it)
        translate([sheet_left - win_clear, sheet_front - win_clear, -1])
            cube([paper_w + 2 * win_clear, paper_h + 2 * win_clear, t + 2]);
    }
}

module lips() {
    translate([plate_x + lip_clear, frame_front, -lip_drop])
        cube([lip_t, outer_y - frame_front, lip_drop + t]);
    translate([frame_left, plate_y + lip_clear, -lip_drop])
        cube([outer_x - frame_left, lip_t, lip_drop + t]);
}

module cutouts() {
    // cut lip AND base overhang at the back edge, from back_lip_end all
    // the way to the right (also trims the right lip's back tip — fine)
    translate([back_lip_end, plate_y - 1, -lip_drop - 1])
        cube([outer_x - back_lip_end + 1, outer_y - plate_y + 2, lip_drop + t + 2]);
}

module jig() {
    difference() {
        union() { base(); lips(); }
        cutouts();
    }
}

// Export in print orientation: rotated 180° about X (a true flip, not a
// mirror), raised so the lowest point sits at z=0.
rotate([180, 0, 0]) translate([0, 0, -t]) jig();
