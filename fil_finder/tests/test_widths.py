
import pytest

from fil_finder.width import nonparam_width, gauss_model, radial_profile

import numpy as np
import numpy.testing as npt
from scipy import ndimage as nd


def generate_filament_model(shape=100, theta=0.0, width=10.0,
                            amplitude=1.0, background=0.0):

    if theta >= np.pi / 2. or theta <= - np.pi / 2.:
        raise ValueError("theta must be between -pi/2 and pi/2")

    yy, xx = np.mgrid[-shape // 2:shape // 2,
                      -shape // 2:shape // 2]

    centers = np.zeros(yy.shape, dtype=bool)
    centers[np.abs(yy - np.tan(theta) * xx) < 1.0] = 1

    radii = nd.distance_transform_edt(centers != amplitude)

    filament = amplitude * np.exp(- (radii ** 2) / (2 * width ** 2)) + \
        background

    return filament, centers


def generate_gaussian_profile(pts, width=3.0, amplitude=2.0, background=0.5):
    return amplitude * np.exp(- pts ** 2 / (2 * width ** 2)) + background


def test_nonparam():

    pts = np.linspace(0, 10, 100)

    profile = generate_gaussian_profile(pts)

    params, errors, fail = \
        nonparam_width(pts, profile, pts, profile, 1.0, 5, 99)

    # This shouldn't be failing
    assert fail is False

    # Check the amplitude
    npt.assert_allclose(params[0], 2.5, atol=0.01)
    # Width
    npt.assert_allclose(params[1], 3.0, atol=0.01)
    # Background
    npt.assert_allclose(params[2], 0.5, atol=0.02)


def test_gaussian():

    pts = np.linspace(0, 10, 100)

    profile = generate_gaussian_profile(pts)

    params, errors, _, _, fail = \
        gauss_model(pts, profile, np.ones_like(pts), 1.0)

    # Check the amplitude
    npt.assert_allclose(params[0], 2.5, atol=0.01)
    # Width
    npt.assert_allclose(params[1], 3.0, atol=0.01)
    # Background
    npt.assert_allclose(params[2], 0.5, atol=0.02)


@pytest.mark.parametrize(('theta'), [(0.0)])
def test_radial_profile_output(theta):

    model, skeleton = generate_filament_model(width=10.0,
                                              amplitude=1.0, background=0.0)

    dist_transform = nd.distance_transform_edt((~skeleton).astype(np.int))

    dist, radprof, weights, unbin_dist, unbin_radprof = \
        radial_profile(model, dist_transform, dist_transform,
                       ((1, 1), (model.shape[0] // 2, model.shape[1] // 2)),
                       img_scale=1.0, auto_cut=False, max_distance=20)

    params, errors, _, _, fail = \
        gauss_model(dist, radprof, np.ones_like(dist), 1.0)

    npt.assert_allclose(params[:-1], [1.0, 10.0, 0.0], atol=1e-1)


@pytest.mark.parametrize(('cutoff'), [(10.0), (20.0), (30.0)])
def test_radial_profile_cutoff(cutoff):

    model, skeleton = generate_filament_model(width=10.0,
                                              amplitude=1.0, background=0.0)

    dist_transform = nd.distance_transform_edt((~skeleton).astype(np.int))

    dist, radprof, weights, unbin_dist, unbin_radprof = \
        radial_profile(model, dist_transform, dist_transform,
                       ((1, 1), (model.shape[0] // 2, model.shape[1] // 2)),
                       img_scale=1.0, auto_cut=False, max_distance=cutoff)

    assert unbin_dist.max() == cutoff
    assert dist.max() < cutoff


@pytest.mark.parametrize(('padding'), [(5.0), (10.0), (20.0)])
def test_radial_profile_padding(padding, max_distance=20.0):

    model, skeleton = generate_filament_model(width=10.0,
                                              amplitude=1.0, background=0.0)

    dist_transform = nd.distance_transform_edt((~skeleton).astype(np.int))

    dist, radprof, weights, unbin_dist, unbin_radprof = \
        radial_profile(model, dist_transform, dist_transform,
                       ((1, 1), (model.shape[0] // 2, model.shape[1] // 2)),
                       img_scale=1.0, auto_cut=False,
                       max_distance=max_distance, pad_to_distance=padding)

    print(padding, unbin_dist.max(), dist.max())

    if padding <= max_distance:
        assert unbin_dist.max() == max_distance
        assert dist.max() < max_distance
    else:
        assert unbin_dist.max() == padding
        assert dist.max() < padding


@pytest.mark.xfail(raises=ValueError)
def test_radial_profile_fail_pad(padding=30.0, max_distance=20.0):
    '''
    Cannot pad greater than max_distance
    '''
    model, skeleton = generate_filament_model(width=10.0,
                                              amplitude=1.0, background=0.0)

    dist_transform = nd.distance_transform_edt((~skeleton).astype(np.int))

    dist, radprof, weights, unbin_dist, unbin_radprof = \
        radial_profile(model, dist_transform, dist_transform,
                       ((1, 1), (model.shape[0] // 2, model.shape[1] // 2)),
                       img_scale=1.0, auto_cut=False,
                       max_distance=max_distance, pad_to_distance=padding)
