# v1.12.1

- TASK-0035: Replace Mercator/sidebar layout with geographic oblique projection and full-width map. Validate left-to-right alignment, orthonormal rotation, dateline handling, equal map scale, visible silhouette movement and preserved station colors. Implemented.
- TASK-0036: Altona continuous model-only motion preview: 300 UTC samples, 12 seconds of playback, original station coordinates and row colors. Preserve skipped-gap semantics in actual station-video exports. All 60 source tests pass; native arm64 package self-tests and GUI startup pass. Real four-station UTC, selected source frames and D/R are identical to the previous export. Versioned local macOS archive packaged. Complete.
