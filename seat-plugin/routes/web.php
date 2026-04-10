<?php

use Illuminate\Support\Facades\Route;
use Volley\SeatVolley\Http\Controllers\VolleyController;

Route::middleware(['web', 'auth'])
    ->prefix('volley')
    ->group(function () {
        Route::get('/', [VolleyController::class, 'index'])->name('volley.index');
        Route::post('/calculate', [VolleyController::class, 'calculate'])->name('volley.calculate');
        Route::post('/fit/resolve', [VolleyController::class, 'resolveFit'])->name('volley.fit.resolve');
        Route::post('/fit/import-zkill', [VolleyController::class, 'importZkill'])->name('volley.fit.import_zkill');
    });
